#!/usr/bin/env python3
# extreme demon roulette, terminal version
# rolls random list positions, you look them up yourself
# first demon needs 1%, each one after needs last % + 1, hit 100 to win
# saves after every input so you can quit whenever
#
# usage:
#   python demon_roulette.py
#   python demon_roulette.py --save other.json

import argparse
import json
import os
import random
from datetime import datetime

# save goes next to the script, not wherever you ran it from
DEFAULT_SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "roulette_save.json")


# save stuff
def save(state, path):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)  # so a crash cant break the save
        return True
    except OSError as e:
        print(f"couldnt save to {path}: {e}")
        return False


def load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        print("save file is broken, ignoring it")
        return None
    # old saves from the first version dont match, skip them
    if not isinstance(state, dict) or "range" not in state:
        print("save file is from an old version, ignoring it")
        return None
    return state


# game stuff
def new_game(lo, hi):
    queue = list(range(lo, hi + 1))
    random.shuffle(queue)
    return {
        "started": datetime.now().isoformat(timespec="seconds"),
        "range": [lo, hi],
        "queue": queue,  # queue[index] is the current demon
        "index": 0,
        "required": 1,
        "history": [],  # {pos, required, got}
        "status": "playing",  # playing / won / gave_up / out
    }


def submit(state, pct):
    # returns an error msg or none
    if not 1 <= pct <= 100:
        return "has to be 1-100"
    if pct < state["required"]:
        return f"need at least {state['required']}%"
    state["history"].append({"pos": state["queue"][state["index"]],
                             "required": state["required"], "got": pct})
    if pct >= 100:
        state["status"] = "won"
        return None
    state["required"] = pct + 1
    state["index"] += 1
    if state["index"] >= len(state["queue"]):
        state["status"] = "out"
    return None


# printing stuff
def show_demon(state):
    n = state["index"] + 1
    pos = state["queue"][state["index"]]
    print(f"\ndemon {n}: #{pos}  (need {state['required']}%)")


def show_history(state):
    if not state["history"]:
        print("nothing yet")
        return
    print(f"\n{'':>3}  {'pos':>5}{'need':>6}{'got':>6}")
    for i, h in enumerate(state["history"], 1):
        print(f"{i:>3}  #{h['pos']:<4}{h['required']:>5}%{h['got']:>5}%")


def show_summary(state):
    show_history(state)
    n = len(state["history"])
    print({
        "won": f"\nwon, hit 100% after {n} demons",
        "gave_up": f"\nover, got through {n}, gave up needing {state['required']}%",
        "out": f"\nran out of demons after {n} lol",
    }[state["status"]])


HELP = """commands:
  <number>  % you got (like 37)
  h         history
  g         give up
  q         save and quit
  ?         this"""


# main
def pick_range():
    print("range of list positions? (like 1-150, blank = 1-75)")
    raw = input("> ").strip()
    if not raw:
        return 1, 75
    try:
        lo, hi = (int(x) for x in raw.split("-"))
        if 1 <= lo <= hi:
            return lo, hi
    except ValueError:
        pass
    print("didnt get that, using 1-75")
    return 1, 75


def play(state, path):
    print(HELP)
    while state["status"] == "playing":
        show_demon(state)
        cmd = input("> ").strip().lower().rstrip("%")
        if cmd in ("q", "quit"):
            if save(state, path):
                print(f"saved to {path}")
            return
        if cmd == "h":
            show_history(state)
            continue
        if cmd == "?":
            print(HELP)
            continue
        if cmd in ("g", "give up"):
            if input("sure? (y/n) ").strip().lower() != "y":
                continue
            state["status"] = "gave_up"
        else:
            try:
                err = submit(state, int(cmd))
            except ValueError:
                print("? for commands")
                continue
            if err:
                print(err)
                continue
        save(state, path)
    save(state, path)
    show_summary(state)


def main():
    ap = argparse.ArgumentParser(description="extreme demon roulette")
    ap.add_argument("--save", default=DEFAULT_SAVE, help="save file")
    args = ap.parse_args()

    state = load(args.save)
    if state and state["status"] == "playing":
        print(f"run in progress, {len(state['history'])} done, "
              f"need {state['required']}%")
        if input("continue? (y/n) ").strip().lower() != "y":
            state = None
    elif state:
        print("last run:")
        show_summary(state)
        state = None

    if state is None:
        if input("new run? (y/n) ").strip().lower() != "y":
            return
        state = new_game(*pick_range())
        save(state, args.save)

    try:
        play(state, args.save)
    except (KeyboardInterrupt, EOFError):
        if save(state, args.save):
            print(f"\nsaved to {args.save}")


if __name__ == "__main__":
    main()
