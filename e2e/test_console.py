"""The operator's console in a real browser. Frame numbers on screen count from 1."""
import re

import pytest
from playwright.sync_api import expect

from conftest import drag_on_picture, shown_frame, upload

text = lambda page, test_id: page.get_by_test_id(test_id)


def load_ref_a(page):
    upload(page, "ref_720p.mp4")
    expect(text(page, "frame-total")).to_have_text("90")
    expect(text(page, "frame-image")).to_be_visible()


def test_nothing_can_be_used_before_a_video_is_loaded(app_url, new_page):                # AC-6.7, AC-7.8, AC-9.4
    page = new_page(app_url)
    expect(text(page, "loaded-name")).to_have_text("No video loaded")
    expect(text(page, "stage-empty")).to_be_visible()
    for control in ("step-back", "step-forward", "play", "slider", "tool-target", "tool-zone", "track"):
        expect(text(page, control)).to_be_disabled()


def test_upload_shows_first_frame_and_metadata(app_url, new_page):                       # AC-1.1, AC-4.1, AC-4.7, AC-6.1, AC-6.10a
    page = new_page(app_url)
    load_ref_a(page)
    expect(text(page, "loaded-name")).to_have_text("ref_720p.mp4")
    expect(text(page, "meta-resolution")).to_have_text("1280 × 720")
    expect(text(page, "meta-fps")).to_have_text("30.00")
    expect(text(page, "meta-duration")).to_have_text("00:03.000")
    expect(text(page, "meta-frames")).to_have_text("90")
    expect(text(page, "frame-number")).to_have_text("1")
    expect(text(page, "frame-time")).to_have_text("00:00.000")
    assert shown_frame(page) == 0
    assert page.get_by_test_id("problem").count() == 0


def test_stepping_and_the_ends_of_the_video(app_url, new_page):                          # AC-6.2, AC-6.3, AC-6.9b/c, AC-6.11a-c
    page = new_page(app_url)
    load_ref_a(page)
    expect(text(page, "step-back")).to_be_disabled()
    expect(text(page, "step-forward")).to_be_enabled()
    text(page, "step-forward").click()
    expect(text(page, "frame-number")).to_have_text("2")
    expect(text(page, "frame-time")).to_have_text("00:00.033")
    expect(text(page, "slider")).to_have_value("1")
    expect(text(page, "step-back")).to_be_enabled()
    assert shown_frame(page) == 1
    text(page, "step-back").click()
    expect(text(page, "frame-number")).to_have_text("1")
    assert shown_frame(page) == 0
    text(page, "slider").fill("89")                                                     # the right end of the slider
    expect(text(page, "frame-number")).to_have_text("90")
    expect(text(page, "frame-time")).to_have_text("00:02.967")
    expect(text(page, "step-forward")).to_be_disabled()
    expect(text(page, "step-back")).to_be_enabled()
    assert shown_frame(page) == 89
    text(page, "slider").fill("88")
    expect(text(page, "frame-number")).to_have_text("89")
    expect(text(page, "step-forward")).to_be_enabled()


def test_slider_then_step_continues_from_there(app_url, new_page):                       # AC-6.9a, AC-6.9d
    page = new_page(app_url)
    load_ref_a(page)
    text(page, "slider").fill("44")
    expect(text(page, "frame-number")).to_have_text("45")
    assert shown_frame(page) == 44
    text(page, "step-forward").click()
    expect(text(page, "frame-number")).to_have_text("46")
    assert shown_frame(page) == 45


def test_picture_and_position_agree_after_rapid_stepping(app_url, new_page):             # AC-6.6
    page = new_page(app_url)
    load_ref_a(page)
    page.evaluate("""() => { const b = document.querySelector('[data-testid="step-forward"]'); for (let i = 0; i < 30; i++) b.click(); }""")
    expect(text(page, "frame-number")).to_have_text("31")
    assert shown_frame(page) == 30
    expect(text(page, "slider")).to_have_value("30")


def test_a_refused_file_lists_every_problem_and_a_good_file_still_loads(app_url, new_page):   # AC-5.6a, AC-4.3, AC-5.1
    page = new_page(app_url)
    upload(page, "three_problems.mp4")
    expect(page.get_by_test_id("problem")).to_have_count(3)
    codes = sorted(item.get_attribute("data-code") for item in page.get_by_test_id("problem").all())
    assert codes == ["resolution", "rotation", "too_short"]
    expect(page.get_by_test_id("problem").filter(has_text="2,073,600 pixels")).to_have_count(1)
    expect(text(page, "loaded-name")).to_have_text("No video loaded")
    expect(text(page, "meta-frames")).to_have_text("—")
    load_ref_a(page)
    expect(page.get_by_test_id("problem")).to_have_count(0)


def test_replacing_a_video_asks_first(app_url, new_page):                                # AC-5.8a, AC-5.8b, AC-5.8c, AC-5.8e
    page = new_page(app_url)
    asked = []
    answers = iter(["dismiss", "accept", "accept"])
    def on_dialog(dialog):
        asked.append(dialog.message)
        getattr(dialog, next(answers))()
    page.on("dialog", on_dialog)
    load_ref_a(page)
    assert asked == []                                                                   # nothing loaded: no question
    text(page, "slider").fill("9")
    expect(text(page, "frame-number")).to_have_text("10")
    upload(page, "ref_360p.mp4")                                                         # declined
    page.wait_for_timeout(300)
    assert len(asked) == 1 and "Replace the loaded video" in asked[0]
    expect(text(page, "loaded-name")).to_have_text("ref_720p.mp4")
    expect(text(page, "frame-number")).to_have_text("10")
    upload(page, "ref_360p.mp4")                                                         # confirmed
    expect(text(page, "loaded-name")).to_have_text("ref_360p.mp4")
    expect(text(page, "meta-resolution")).to_have_text("640 × 360")
    expect(text(page, "frame-number")).to_have_text("1")
    upload(page, "notes.txt", data=b"flight notes\n")                                    # confirmed, but refused by the checks
    expect(page.get_by_test_id("problem")).to_have_count(1)
    expect(text(page, "loaded-name")).to_have_text("ref_360p.mp4")                      # the loaded video stays
    expect(text(page, "meta-frames")).to_have_text("50")


def test_messages_and_numbers_are_english_in_a_turkish_browser(app_url, new_page):       # AC-5.6c
    page = new_page(app_url, locale="tr-TR")
    upload(page, "res_1920x1080.mp4")
    expect(page.get_by_test_id("problem")).to_contain_text("2,073,600 pixels")
    expect(page.get_by_test_id("problem")).to_contain_text("The resolution is larger than the maximum allowed")
    upload(page, "long_720p_10min.mp4")
    expect(text(page, "meta-frames")).to_have_text("18,000")
    expect(text(page, "meta-fps")).to_have_text("30.00")
    expect(text(page, "meta-duration")).to_have_text("10:00.000")


def test_variable_frame_rate_shows_the_average_and_a_warning(app_url, new_page):         # AC-4.4a, AC-6.10c
    page = new_page(app_url)
    upload(page, "vfr_720p.mp4")
    expect(text(page, "meta-fps")).to_have_text("20.00")
    expect(page.get_by_text("Frame rate (average)")).to_be_visible()
    expect(page.get_by_test_id("warning")).to_contain_text("variable frame rate")
    text(page, "slider").fill("59")
    expect(text(page, "frame-number")).to_have_text("60")
    expect(text(page, "frame-time")).to_have_text("00:02.950")


def test_a_frame_that_cannot_be_read_warns_and_keeps_the_position(app_url, new_page):    # AC-5.7, AC-6.9g, AC-6.11d, AC-6.11e
    page = new_page(app_url)
    upload(page, "damaged_720p.mp4")
    expect(text(page, "frame-total")).to_have_text("90")                                # the header's number (OQ-8)
    text(page, "slider").fill("4")
    expect(text(page, "frame-number")).to_have_text("5")
    text(page, "slider").fill("89")                                                     # a frame that cannot be read
    expect(page.get_by_test_id("warning")).to_contain_text("cannot be read")
    expect(page.get_by_test_id("warning")).to_contain_text("damaged")
    expect(text(page, "frame-number")).to_have_text("5")                                # still the last frame shown
    expect(text(page, "slider")).to_have_value("4")                                     # the slider came back
    assert shown_frame(page) == 4
    text(page, "step-back").click()
    expect(text(page, "frame-number")).to_have_text("4")                                # and stepping still works


def test_draw_target_and_zone_track_and_read_the_result(app_url, new_page):              # AC-7.1, AC-7.3, AC-8, AC-9, AC-10.1, AC-11, AC-14, AC-15
    page = new_page(app_url)
    load_ref_a(page)
    expect(text(page, "track")).to_be_disabled()                                        # no target yet
    drag_on_picture(page, (100, 292), (196, 358))                                       # around the white marker of frame 1
    expect(text(page, "track")).to_be_enabled()
    state = page.evaluate("async () => (await (await fetch('/api/video')).json()).video.id")
    stored = page.evaluate("async id => (await (await fetch(`/api/video/${id}/tracking`)).json())", state)
    assert stored["target"]["frame"] == 0
    assert [round(v) for v in stored["target"]["box"]] == [100, 292, 96, 66]            # picture pixels, not screen pixels
    expect(text(page, "zone-state")).to_have_attribute("data-zone", "none")             # no zone yet: say so
    expect(text(page, "zone-state")).to_contain_text("No lock zone")
    text(page, "tool-zone").click()
    drag_on_picture(page, (300, 200), (700, 500))
    expect(text(page, "zone-state")).to_have_attribute("data-zone", "drawn")
    expect(text(page, "zone-state")).to_contain_text("400 × 300")
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "completed", timeout=60_000)
    expect(text(page, "run-progress")).to_contain_text("90 / 90")
    assert float(text(page, "run-fps").inner_text().split()[0]) > 0
    # The marker moves right 8 px per frame: it is inside the zone (x 300 to 700) from about frame 26 to 64.
    statuses = [segment.get_attribute("data-status") for segment in page.get_by_test_id("timeline-segment").all()]
    assert statuses == ["unlocked", "locked", "unlocked"]
    locked = page.get_by_test_id("timeline-segment").nth(1)
    assert 22 <= int(locked.get_attribute("data-start")) <= 28 and 60 <= int(locked.get_attribute("data-end")) <= 66
    expect(text(page, "lock-periods")).to_have_text("1")
    assert 1.1 <= float(text(page, "total-locked").inner_text().split()[0]) <= 1.5
    assert text(page, "longest-lock").inner_text() == text(page, "average-lock").inner_text()       # one period only
    expect(text(page, "status")).to_have_text("UNLOCKED")                               # frame 1
    text(page, "slider").fill("44")
    expect(text(page, "status")).to_have_text("LOCKED")                                 # frame 45
    expect(text(page, "status")).to_have_css("color", "rgb(70, 185, 120)")              # green
    # The box drawn on frame 45 is where the marker is: green pixels on its left edge, none far away.
    green = page.evaluate("""(x) => { const c = document.querySelector('[data-testid="overlay"]'); const s = c.width / 1280;
        const d = c.getContext('2d').getImageData(Math.round((x - 12) * s), Math.round(325 * s), Math.round(24 * s), 1).data;
        let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i + 1] > 150 && d[i] < 120 && d[i + 3] > 0) n++; return n; }""", 108 + 8 * 44)
    assert green > 0
    page.screenshot(path=str(__import__("pathlib").Path(__file__).parent / "artifacts" / "console.png"))


# On some machines (seen on Windows) the player's clock, currentTime, lags the frame
# the browser has just put on screen. This script makes it lag by 40 ms, a bit more than
# one frame at 30 fps, so the test sees what such a machine sees.
LAGGING_CLOCK = """
(() => {
  const real = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, "currentTime");
  Object.defineProperty(HTMLMediaElement.prototype, "currentTime", {
    configurable: true,
    get() { return Math.max(0, real.get.call(this) - 0.04); },
    set(value) { real.set.call(this, value); },
  });
})();
"""


@pytest.mark.parametrize("clock", ["exact", "lagging"])
def test_playback_draws_over_the_player_and_stops_on_an_exact_frame(app_url, new_page, clock):  # AC-9.2, AC-9.4
    page = new_page(app_url, init_script=LAGGING_CLOCK if clock == "lagging" else None)
    load_ref_a(page)
    text(page, "play").click()
    expect(text(page, "play")).to_have_text("Pause")
    expect(text(page, "frame-image")).to_have_count(0)                                  # the player is showing, not a still
    expect(text(page, "frame-number")).not_to_have_text("1", timeout=10_000)            # the position follows the player
    page.wait_for_timeout(500)
    # Press Pause and, in the same instant, read the frame number the operator was looking at.
    seen = int(page.evaluate("""() => {
        document.querySelector('[data-testid="play"]').click();
        return document.querySelector('[data-testid="frame-number"]').textContent; }"""))
    expect(text(page, "play")).to_have_text("Play")
    expect(text(page, "frame-image")).to_be_visible()
    expect(text(page, "slider")).to_have_value(str(seen - 1))
    for _ in range(3):                      # nothing may move the position after Pause
        page.wait_for_timeout(300)
        assert int(text(page, "frame-number").inner_text()) == seen                     # Pause keeps the frame on screen
        assert shown_frame(page) == seen - 1                                            # and the still is exactly that frame


def test_loss_is_shown_and_tracking_resumes_from_a_new_box(scripted_url, new_page):      # AC-12.1, AC-12.5, AC-13.1
    page = new_page(scripted_url)
    load_ref_a(page)
    drag_on_picture(page, (100, 292), (196, 358))
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "lost")
    expect(text(page, "lost-message")).to_contain_text("frame 41")
    expect(text(page, "lost-message")).to_contain_text("tracker reported failure")
    expect(text(page, "zone-state")).to_have_attribute("data-zone", "none")             # tracked without a zone: still said
    expect(text(page, "frame-number")).to_have_text("41")                               # the page went to the frame of the loss
    expect(text(page, "status")).to_have_text("LOST")
    expect(text(page, "status")).to_have_css("color", "rgb(229, 83, 75)")               # red
    expect(text(page, "track")).to_have_text(re.compile("Resume tracking"))
    for _ in range(5):
        text(page, "step-forward").click()
    expect(text(page, "frame-number")).to_have_text("46")
    drag_on_picture(page, (460, 292), (556, 358))                                       # a new box on frame 46
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "completed")
    segments = [(s.get_attribute("data-status"), int(s.get_attribute("data-start")), int(s.get_attribute("data-end")))
                for s in page.get_by_test_id("timeline-segment").all()]
    assert segments == [("unlocked", 0, 39), ("lost", 40, 44), ("unlocked", 45, 89)]    # frames 41-45 stay LOST
    expect(text(page, "total-lost")).to_contain_text("(5 fr)")
    assert page.get_by_test_id("lost-message").count() == 0


def test_ac_16_telemetry_of_the_frame_shown(scripted_url, new_page):                      # AC-16.1, AC-16.3, AC-16.5
    page = new_page(scripted_url)                       # stand-in tracker: box (100 + 8i, 292, 96, 66), lost on frame 41
    load_ref_a(page)
    expect(text(page, "tele-centre")).to_have_text("—")
    drag_on_picture(page, (100, 292), (196, 358))
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "lost")
    expect(text(page, "tele-centre")).to_have_text("—")                                 # frame 41 is LOST: no box
    text(page, "slider").fill("10")
    expect(text(page, "frame-number")).to_have_text("11")
    expect(text(page, "tele-centre")).to_have_text("228, 325")
    expect(text(page, "tele-size")).to_have_text("96 × 66")
    expect(text(page, "tele-area")).to_have_text("6,336 px²")
    expect(text(page, "tele-change")).to_have_text("0.0 %")
    expect(text(page, "tele-margin")).to_have_text("No lock zone")
    text(page, "slider").fill("0")
    expect(text(page, "tele-change")).to_have_text("—")                                 # first frame of the run
    text(page, "tool-zone").click()
    drag_on_picture(page, (50, 250), (450, 450))                                        # zone x 50..450, y 250..450
    expect(text(page, "tele-margin")).to_have_text("42 px inside")                      # top: 292 - 250 = 42 is the smallest


def test_ac_17_play_waits_for_tracking_and_unreached_frames_say_so(slow_url, new_page):   # AC-17.1, AC-17.2
    page = new_page(slow_url)
    load_ref_a(page)
    expect(text(page, "play")).to_be_enabled()
    drag_on_picture(page, (100, 292), (196, 358))
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "running")
    expect(text(page, "play")).to_be_disabled()
    expect(text(page, "play")).to_have_attribute("title", re.compile("tracking"))
    text(page, "slider").fill("85")
    expect(text(page, "status")).to_have_text("Not tracked yet")
    expect(text(page, "run-state")).to_have_attribute("data-state", "completed", timeout=30_000)
    expect(text(page, "play")).to_be_enabled()
    expect(text(page, "status")).to_have_text("UNLOCKED")                               # the frame now has a result


def test_ac_18_timeline_has_a_time_scale_and_numbered_periods(scripted_url, new_page):    # AC-18.1, AC-18.2
    page = new_page(scripted_url)
    load_ref_a(page)                                                                    # 3.0 s: marks every 0.5 s
    labels = [t.inner_text() for t in page.get_by_test_id("timeline-tick").all()]
    assert labels == ["0.0 s", "0.5 s", "1.0 s", "1.5 s", "2.0 s", "2.5 s", "3.0 s"]
    text(page, "tool-zone").click()
    drag_on_picture(page, (100, 250), (500, 420))                                       # box (100 + 8i, ...) inside while i <= 38
    text(page, "tool-target").click()
    drag_on_picture(page, (100, 292), (196, 358))
    text(page, "track").click()
    expect(text(page, "run-state")).to_have_attribute("data-state", "lost")
    expect(page.get_by_test_id("period-number")).to_have_count(1)
    expect(page.get_by_test_id("period-number")).to_have_text("1")
    expect(text(page, "lock-periods")).to_have_text("1")
