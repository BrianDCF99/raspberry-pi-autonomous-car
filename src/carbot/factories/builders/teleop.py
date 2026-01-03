from carbot.config.loader import load_teleop_config
from carbot.inputs.teleop import Teleop 
from carbot.inputs.terminal_kb_teleop import TerminalKeyboardTeleop
from carbot.inputs.usb_kb_teleop import UsbKeyboardTeleop

def build_teleop(*, keyboard: str, cfg_name_or_path: str) -> Teleop:
    cfg = load_teleop_config(cfg_name_or_path)

    if keyboard == "terminal":
        return TerminalKeyboardTeleop(cfg)

    if keyboard == "usb":
        return UsbKeyboardTeleop(cfg)

    raise ValueError(f"Unknown keyboard kind: {keyboard!r} (expected 'usb' or 'terminal')")