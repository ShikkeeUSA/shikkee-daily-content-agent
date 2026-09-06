"""
HeyGen persona configuration. Look IDs are the Tal-approved sets as of 2026-09-04 --
refresh this file (not a dynamic list_avatar_looks() call) whenever Tal approves a
new set, per the STANDING RULE that dynamic lookup is deprecated for routine use.

FOUNDER AVATAR VIDEO DISCONTINUED (2026-09-06, per Tal's explicit instruction):
TAL_LEVI and AYALA_CHRYSLER below are no longer used to generate video -- the
Founder Slay and Founder Expert Numbers tracks (pipeline/founder_tracks.py) are
written-only now (LinkedIn/X copy, no HeyGen call at all). They're kept here
for historical reference only; do not wire them back into a video call without
a fresh, explicit instruction from Tal. ELLA is unaffected and is now the only
persona this codebase generates video for (six_channel.py, Instagram/YouTube).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    group_id: str
    default_voice: str
    approved_looks: tuple[str, ...]
    flagged_looks: tuple[str, ...] = ()


ELLA = Persona(
    name="Ella",
    group_id="d1f6ef33624a4c47940e308a360aa8c4",
    default_voice="65a5fc7e561b4914af87ce8a28b76bd2",
    approved_looks=(
        "44f9abc8fe0140c3b53f27439f1ec9a7",
        "4418028ad348441f9b88c54197868f09",
        "00942770b93c441fb7eb23e09b5dc1fd",
        "be0298c212804e5898e6779914181963",
        "280b52c8e6dd42cdb37afaee52cdda59",
    ),
)

TAL_LEVI = Persona(
    name="Tal Levi",
    group_id="622fd8c3fcfb45118f20f789ff8623a0",
    default_voice="390cbaee387b49119fd9db1ec65270ff",
    approved_looks=(
        "66fad592ca524617a7e6571d8bc76a6c",
        "a84d07d211f648428b2570f0ea16283a",
        "45dc03cdb32a40859ccc7f2fb48afe9d",
        "17e8b3be54774d01af1b4f4b9d934dfe",
    ),
    # a84d07... has been flagged twice for rendering issues (see HeyGen avatar
    # usage notes in project history) -- prefer the other three until re-verified.
    flagged_looks=("a84d07d211f648428b2570f0ea16283a",),
)

AYALA_CHRYSLER = Persona(
    name="Ayala Chrysler",
    group_id="bda85643719b483fab1451d1a57ec763",
    default_voice="2fb02cec7e7c4790a91d3392803a7462",
    approved_looks=(
        "75fff02922ce4b908d26499ca6f6e456",
        "631361f7bd4a4bd19908834db688ee06",
        "01b1e185b4ad4752a7277afe9051f645",
        "4fb5330a917d4f9190b876b6faf15bef",
        "b8aeb3a23c34471f8190769609399a01",
    ),
)

PERSONAS_BY_NAME = {
    "Ella": ELLA,
    "Tal Levi": TAL_LEVI,
    "Ayala Chrysler": AYALA_CHRYSLER,
}
