#!/usr/bin/env python3
"""
Test script for BLE protocol functions

This script tests the protocol mappings and helper functions
without requiring actual BLE hardware.
"""

import protocol

def test_patterns():
    """Test pattern name/index mappings"""
    print("Testing Pattern Mappings:")
    print("=" * 50)

    # Test forward mapping (index -> name)
    test_indices = [0, 1, 14, 18, 33, 36]
    for idx in test_indices:
        name = protocol.get_pattern_name(idx)
        print(f"  Index {idx:2d} -> {name}")

    print()

    # Test reverse mapping (name -> index)
    test_names = ["red", "rainbow", "snow", "elapsed", "lava_lamp"]
    for name in test_names:
        idx = protocol.get_pattern_index(name)
        print(f"  Name '{name}' -> Index {idx}")

    print()

    # Test invalid cases
    print("  Invalid index 99 ->", protocol.get_pattern_name(99))
    print("  Invalid name 'foobar' ->", protocol.get_pattern_index("foobar"))
    print()

def test_games():
    """Test game name/index mappings"""
    print("Testing Game Mappings:")
    print("=" * 50)

    for idx in range(len(protocol.GAMES)):
        name = protocol.get_game_name(idx)
        print(f"  Index {idx} -> {name}")

    print()
    print("  Invalid index 99 ->", protocol.get_game_name(99))
    print()

def test_actions():
    """Test action name/index mappings"""
    print("Testing Action Mappings:")
    print("=" * 50)

    for idx in range(len(protocol.ACTIONS)):
        name = protocol.get_action_name(idx)
        print(f"  Index {idx} -> {name}")

    print()
    print("  Invalid index 99 ->", protocol.get_action_name(99))
    print()

def test_constants():
    """Test protocol constants"""
    print("Testing Protocol Constants:")
    print("=" * 50)
    print(f"  Service UUID: {protocol.SERVICE_UUID}")
    print(f"  Max Chunk Size: {protocol.MAX_CHUNK_SIZE} bytes")
    print(f"  Frame Timeout: {protocol.FRAME_TIMEOUT} seconds")
    print(f"  Total Patterns: {len(protocol.PATTERNS)}")
    print(f"  Total Games: {len(protocol.GAMES)}")
    print(f"  Total Actions: {len(protocol.ACTIONS)}")
    print()

def test_uuids():
    """Test all characteristic UUIDs are unique"""
    print("Testing UUID Uniqueness:")
    print("=" * 50)

    uuids = [
        ("Service", protocol.SERVICE_UUID),
        ("Brightness", protocol.CHAR_BRIGHTNESS_UUID),
        ("Pattern", protocol.CHAR_PATTERN_UUID),
        ("Game Control", protocol.CHAR_GAME_CONTROL_UUID),
        ("Status", protocol.CHAR_STATUS_UUID),
        ("Config", protocol.CHAR_CONFIG_UUID),
        ("Power Limit", protocol.CHAR_POWER_LIMIT_UUID),
        ("Sleep Schedule", protocol.CHAR_SLEEP_SCHEDULE_UUID),
        ("Frame Stream", protocol.CHAR_FRAME_STREAM_UUID),
    ]

    uuid_set = set()
    for name, uuid in uuids:
        print(f"  {name:15s}: {uuid}")
        if uuid in uuid_set:
            print(f"    ERROR: Duplicate UUID!")
        uuid_set.add(uuid)

    print()
    if len(uuid_set) == len(uuids):
        print("  ✓ All UUIDs are unique")
    else:
        print("  ✗ Duplicate UUIDs found!")
    print()

def main():
    """Run all tests"""
    print()
    print("BLE Protocol Test Suite")
    print("=" * 50)
    print()

    test_constants()
    test_uuids()
    test_patterns()
    test_games()
    test_actions()

    print("=" * 50)
    print("All tests complete!")
    print()

if __name__ == "__main__":
    main()
