package com.hagoyama;

import java.util.SplittableRandom;

/**
 * Where the cave shrines are. There is exactly one shrine per REGION x REGION chunk square and its spot
 * is a pure function of the world seed, so the world generator and /hagoyama locate always agree - even
 * for chunks nobody has visited yet. No Minecraft classes in here on purpose (it is unit-tested alone).
 */
public final class ShrineLocator {
    /** Region size in chunks (12 chunks = 192 blocks). */
    public static final int REGION = 12;
    /** Keeps a site this many chunks away from its region edge, so neighbouring shrines never touch. */
    public static final int MARGIN = 3;
    public static final int MIN_Y = -40;
    public static final int MAX_Y = 10;

    public record Site(int chunkX, int chunkZ, int y) {
        public int blockX() { return chunkX * 16 + 8; }
        public int blockZ() { return chunkZ * 16 + 8; }
    }

    private ShrineLocator() { }

    private static long mix(long seed, int a, int b) {
        long h = seed;
        h ^= a * 0x9E3779B97F4A7C15L;
        h = Long.rotateLeft(h, 31) * 0xBF58476D1CE4E5B9L;
        h ^= b * 0x94D049BB133111EBL;
        h = Long.rotateLeft(h, 27) * 0x9E3779B97F4A7C15L;
        h ^= h >>> 33;
        return h;
    }

    /** The shrine site of one region. */
    public static Site siteOfRegion(long seed, int regionX, int regionZ) {
        SplittableRandom r = new SplittableRandom(mix(seed ^ 0x5DEECE66DL, regionX, regionZ));
        int span = REGION - 2 * MARGIN;
        int cx = regionX * REGION + MARGIN + r.nextInt(span);
        int cz = regionZ * REGION + MARGIN + r.nextInt(span);
        int y = MIN_Y + r.nextInt(MAX_Y - MIN_Y + 1);
        return new Site(cx, cz, y);
    }

    /** The site that generates in this chunk, or null when this chunk holds no shrine. */
    public static Site siteInChunk(long seed, int chunkX, int chunkZ) {
        Site s = siteOfRegion(seed, Math.floorDiv(chunkX, REGION), Math.floorDiv(chunkZ, REGION));
        return s.chunkX() == chunkX && s.chunkZ() == chunkZ ? s : null;
    }

    /** The shrine closest to a block position. Looking two regions out in every direction is always enough. */
    public static Site nearest(long seed, double blockX, double blockZ) {
        int rx = Math.floorDiv(((int) Math.floor(blockX)) >> 4, REGION);
        int rz = Math.floorDiv(((int) Math.floor(blockZ)) >> 4, REGION);
        Site best = null;
        double bestD = Double.MAX_VALUE;
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                Site s = siteOfRegion(seed, rx + dx, rz + dz);
                double d = Math.hypot(s.blockX() - blockX, s.blockZ() - blockZ);
                if (d < bestD) { bestD = d; best = s; }
            }
        }
        return best;
    }
}
