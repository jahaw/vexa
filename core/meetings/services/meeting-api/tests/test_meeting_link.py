"""Unit tests for ``collector.meeting_link.parse_meeting_url`` — the pasted-link →
``(platform, native_meeting_id)`` oracle (the server twin of the terminal's
``parseMeetingInput``). Route-level coverage rides test_planned_meetings.py /
test_calendar_sync.py; this file pins the per-platform parse table directly,
with jitsi as the newest row. Pure string logic — no app, no DB.
"""
from __future__ import annotations

from meeting_api.bot_spawn.service import construct_meeting_url
from meeting_api.collector.meeting_link import find_meeting_link, parse_meeting_url


class TestParseJitsi:
    def test_canonical_room(self):
        assert parse_meeting_url("https://meet.jit.si/VexaStandup") == ("jitsi", "VexaStandup")

    def test_room_case_preserved(self):
        assert parse_meeting_url("https://meet.jit.si/MyRoom") == ("jitsi", "MyRoom")

    def test_trailing_slash(self):
        assert parse_meeting_url("https://meet.jit.si/MyRoom/") == ("jitsi", "MyRoom")

    def test_url_encoded_room_stays_encoded(self):
        # The native id is embedded back into URL templates / path params, so the
        # percent-encoded form IS the id — decoding would corrupt the round-trip.
        assert parse_meeting_url("https://meet.jit.si/Team%20Sync") == ("jitsi", "Team%20Sync")

    def test_bare_origin_rejected(self):
        assert parse_meeting_url("https://meet.jit.si/") is None

    def test_multi_segment_path_rejected(self):
        assert parse_meeting_url("https://meet.jit.si/a/b") is None

    def test_self_hosted_jitsi_host_inferred(self):
        # A host naming jitsi is a jitsi deployment; the caller keeps the raw URL as
        # meeting_url so the bot joins on that host, not the meet.jit.si template.
        # The native id embeds the host (room@host) — a jitsi room is deployment-scoped,
        # so same-named rooms on different deployments never share an identity key.
        assert parse_meeting_url("https://jitsi.example.org/MyRoom") == ("jitsi", "MyRoom@jitsi.example.org")

    def test_self_hosted_meet_convention_inferred_on_paste(self):
        assert parse_meeting_url("https://meet.example.org/TeamSync") == ("jitsi", "TeamSync@meet.example.org")
        # Regionalized deployments put "meet" mid-hostname.
        assert parse_meeting_url("https://eu.meet.example.org/QualifiedRoomName") == (
            "jitsi",
            "QualifiedRoomName@eu.meet.example.org",
        )
        # "meet" must be a whole label — meetings.example.org is NOT a jitsi convention.
        assert parse_meeting_url("https://meetings.example.org/Room") is None
        # …and NOT in the free-text (ICS) scan, where the meet-label rule is too loose.
        assert parse_meeting_url("https://eu.meet.example.org/TeamSync", generic_hosts=False) is None
        # meet.google.com is claimed by the Meet rule first — never captured by the fallback.
        assert parse_meeting_url("https://meet.google.com/abc-defg-hij") == ("google_meet", "abc-defg-hij")


class TestParseExistingPlatformsUnchanged:
    def test_gmeet(self):
        assert parse_meeting_url("https://meet.google.com/abc-defg-hij") == ("google_meet", "abc-defg-hij")

    def test_zoom(self):
        assert parse_meeting_url("https://us05web.zoom.us/j/84335626851?pwd=x") == ("zoom", "84335626851")

    def test_teams_short(self):
        assert parse_meeting_url("https://teams.live.com/meet/9361792952021?p=abc") == ("teams", "9361792952021")


class TestFindMeetingLinkJitsi:
    def test_found_in_free_text(self):
        got = find_meeting_link("Join us: https://meet.jit.si/VexaStandup today")
        assert got == ("jitsi", "VexaStandup", "https://meet.jit.si/VexaStandup")

    def test_meet_label_host_not_imported_from_free_text(self):
        # The meet-label convention is pasted-link-only — an ICS full of arbitrary
        # links must not guess rooms. Declaring the host (below) is the opt-in.
        assert find_meeting_link("agenda: https://eu.meet.example.org/Weekly") is None


class TestConfiguredJitsiHosts:
    def test_declared_host_parses_and_imports(self, monkeypatch):
        monkeypatch.setenv("VEXA_JITSI_HOSTS", "eu.meet.example.org, calls.example.io")
        # Pasted link on a declared host — parses in strict mode too. Declared or not, a
        # non-canonical deployment's native id stays deployment-scoped (room@host).
        assert parse_meeting_url("https://eu.meet.example.org/Weekly", generic_hosts=False) == (
            "jitsi",
            "Weekly@eu.meet.example.org",
        )
        # A declared host with NO jitsi/meet naming at all.
        assert parse_meeting_url("https://calls.example.io/Standup", generic_hosts=False) == (
            "jitsi",
            "Standup@calls.example.io",
        )
        # Calendar (ICS) free-text scan now imports it — the point of the setting.
        got = find_meeting_link("agenda: https://eu.meet.example.org/Weekly today")
        assert got == ("jitsi", "Weekly@eu.meet.example.org", "https://eu.meet.example.org/Weekly")

    def test_unset_env_declares_nothing(self, monkeypatch):
        monkeypatch.delenv("VEXA_JITSI_HOSTS", raising=False)
        assert parse_meeting_url("https://calls.example.io/Standup") is None


class TestConstructMeetingUrl:
    def test_jitsi_requires_explicit_url(self):
        # A jitsi room name is deployment-scoped — constructing a URL from the bare id
        # would join the PUBLIC meet.jit.si room of that name (the wrong meeting), so
        # jitsi has no template: callers pass meeting_url, like zoom.
        assert construct_meeting_url("jitsi", "VexaStandup") is None

    def test_zoom_still_requires_explicit_url(self):
        assert construct_meeting_url("zoom", "84335626851") is None


class TestParseZoomHostedDomain:
    """Zoom served under somebody else's hostname — the twin of the MCP link parser's
    hosted-domain branch (fr_042129f5d53aa543), kept in step with it deliberately: the two
    parsers answer the same question on two doors, and a link that parses on one and 422s on the
    other is the worst of both.

    Matched on the PATH SHAPE plus a passcode parameter, never on the hostname — the hostname is
    the part a hosted front door replaces.
    """

    LFX = ("https://zoom-lfx.platform.linuxfoundation.org/meeting/96088138284"
           "?password=placeholder-passcode-not-a-secret")

    def test_the_linux_foundation_link(self):
        assert parse_meeting_url(self.LFX) == ("zoom", "96088138284")

    def test_a_host_that_does_not_say_zoom_at_all(self):
        assert parse_meeting_url("https://meetings.example.org/j/98765432101?pwd=placeholder-pwd") == (
            "zoom", "98765432101",
        )

    def test_without_a_passcode_it_is_not_claimed(self):
        """The negative case: a bare numeric path on an unknown host is not a meeting."""
        assert parse_meeting_url("https://meetings.example.org/meeting/98765432101") is None

    def test_an_ordinary_page_with_a_number_in_it_is_not_claimed(self):
        assert parse_meeting_url("https://news.example.org/article/96088138284?password=x") is None

    def test_the_ics_free_text_scan_does_not_infer_it(self):
        """``generic_hosts=False`` exists so a calendar description full of arbitrary links does
        not import one as a meeting; a hostname-free inference is exactly what it excludes."""
        hostname_free = "https://meetings.example.org/j/98765432101?pwd=placeholder-pwd"
        assert parse_meeting_url(hostname_free, generic_hosts=False) is None
        assert find_meeting_link(f"join here {hostname_free} thanks") is None
        # The LFX host is a different case and is unaffected: it literally contains "zoom", so the
        # long-standing hostname branch claims it in every mode, free-text scan included.
        assert find_meeting_link(f"join here {self.LFX} thanks") == (
            "zoom", "96088138284", self.LFX,
        )

    def test_a_declared_jitsi_host_is_not_overruled(self, monkeypatch):
        monkeypatch.setenv("VEXA_JITSI_HOSTS", "video.corp.example")
        assert parse_meeting_url("https://video.corp.example/j/12345678901?pwd=x") is None


class TestHostnameSpoofing:
    """A hostname matched by SUBSTRING can be spoofed from both ends, and both ends are cheap:
    the attacker owns the registrable domain in ``teams.live.com.evil.example`` and owns the
    label in ``evilteams.live.com``. Either one used to satisfy ``"teams.live.com" in host``.
    The parser now compares the parsed ``hostname`` exactly, or as a dot-separated subdomain of
    a listed host (CodeQL py/incomplete-url-substring-sanitization).

    The assertion that matters is that the spoof is not answered with the REAL platform — a
    caller acting on ``("teams", <id>)`` sends a bot to Microsoft on an attacker's say-so.
    """

    def test_google_meet_suffix_spoof_is_not_google_meet(self):
        # Falls through to the pasted-link jitsi naming heuristic (the host does carry a "meet"
        # label), which is honest about what it is — what it must never do is claim google_meet.
        got = parse_meeting_url("https://meet.google.com.evil.example/abc-defg-hij")
        assert got != ("google_meet", "abc-defg-hij")
        assert got is None or got[0] == "jitsi"

    def test_google_meet_in_the_path_is_not_google_meet(self):
        assert parse_meeting_url("https://evil.example/meet.google.com/abc-defg-hij") is None

    def test_teams_suffix_spoof_is_not_claimed(self):
        assert parse_meeting_url(
            "https://teams.live.com.evil.example/l/meetup-join/19:meeting_AbCd@thread.v2"
        ) is None
        assert parse_meeting_url(
            "https://teams.microsoft.com.evil.example/meet/9361792952021?p=x"
        ) is None

    def test_teams_prefix_spoof_is_not_claimed(self):
        assert parse_meeting_url("https://eviltteams.live.com/meet/9361792952021?p=x") is None
        assert parse_meeting_url("https://notteams.microsoft.com/meet/9361792952021?p=x") is None

    def test_real_teams_subdomains_still_parse(self):
        assert parse_meeting_url("https://teams.live.com/meet/9361792952021?p=abc") == (
            "teams", "9361792952021",
        )
        assert parse_meeting_url("https://eu.teams.microsoft.com/meet/9361792952021?p=abc") == (
            "teams", "9361792952021",
        )

    def test_google_meet_itself_still_parses(self):
        assert parse_meeting_url("https://meet.google.com/abc-defg-hij") == (
            "google_meet", "abc-defg-hij",
        )


class TestTeamsThreadIdIsBounded:
    """The thread-id scan runs ``.search()`` over caller-supplied text, so the repeat is bounded
    (CodeQL py/polynomial-redos). The bound is far above any real id; what it removes is the
    quadratic retry an attacker-chosen string would otherwise buy."""

    def test_a_realistic_thread_id_parses(self):
        thread = "19:meeting_" + "M" * 90 + "@thread.v2"
        assert parse_meeting_url(f"https://teams.microsoft.com/l/meetup-join/{thread}") == (
            "teams", thread,
        )

    def test_an_adversarial_string_terminates(self):
        import time

        payload = "19:meeting_" + "a" * 40000
        start = time.monotonic()
        assert parse_meeting_url(f"https://teams.microsoft.com/l/meetup-join/{payload}") is None
        assert time.monotonic() - start < 2.0


class TestTeamsThreadTenantSegment:
    """【旧版深链·租户中段兼容】新版 Teams 深链的 thread id 在 ``19:`` 与 ``meeting_`` 之间
    存在一段租户中段（``19:gal:meeting_…@thread.v2``，中国区/世纪互联租户常见）。该形态此前
    无法被识别 → POST /meetings（计划会议）统一 422 "unrecognized 'meeting_url'"，预定会议
    创建即失败、到点自然无法入会；而"添加 Bot"链路因前端携带完整深链（meeting_url 原样直达）
    不经服务端解析，不受影响——两条链路行为不一致的唯一根因即此。回归锁定：识别结果为完整
    thread id（含中段），与前端 lib/meeting-input.ts 的解析口径一致。"""

    def test_china_cloud_tenant_segment_deep_link_parses(self):
        # 用户实测报障的原始链接（中国区域名 + percent-encoded thread id，含 gal: 租户中段）
        url = (
            "https://teams.microsoftonline.cn/l/meetup-join/"
            "19%3agal%3ameeting_fdf65fc8cb8d43c5bf6407bec5c998a8%40thread.v2/0"
            "?context=%7b%22Tid%22%3a%226ce77474-4394-4c4c-889c-193827a4c1fb%22%2c"
            "%22Oid%22%3a%22f8429c18-cd88-4e69-88cf-cc6e09027e1a%22%7d"
        )
        assert parse_meeting_url(url) == (
            "teams",
            "19:gal:meeting_fdf65fc8cb8d43c5bf6407bec5c998a8@thread.v2",
        )

    def test_classic_thread_id_still_parses_unchanged(self):
        # 经典形态（无租户中段）回归：group(0) 提取口径不变
        assert parse_meeting_url(
            "https://teams.microsoft.com/l/meetup-join/19:meeting_AbCd@thread.v2"
        ) == ("teams", "19:meeting_AbCd@thread.v2")

    def test_channel_style_id_is_still_not_a_meeting(self):
        # 频道会议 id（19:<频道名>@thread.tacv2）不含 meeting_，仍不识别（无误报扩散）
        assert parse_meeting_url(
            "https://teams.microsoft.com/l/meetup-join/19:channel@thread.tacv2/0"
        ) is None

    def test_spoofed_host_with_tenant_segment_is_still_rejected(self):
        # 域名白名单逻辑不受放宽影响：仿冒域名上的深链仍拒绝
        assert parse_meeting_url(
            "https://teams.live.com.evil.example/l/meetup-join/19:gal:meeting_AbCd@thread.v2"
        ) is None

