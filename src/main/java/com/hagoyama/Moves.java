package com.hagoyama;

/** Add new moves here. The switch keybind cycles through this list in order. */
public enum Moves {
    CLEAR_EYE("Clear Eye", "See in the dark, see mob health, and zoom in.");

    public final String display;
    public final String description;

    Moves(String display, String description) {
        this.display = display;
        this.description = description;
    }

    public static Moves get(int index) {
        return values()[Math.floorMod(index, values().length)];
    }
}
