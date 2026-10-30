import com.hagoyama.ShrineLocator;
import java.util.Random;

/** Pure-Java tests for the shrine placement math. Run with the classpath containing ShrineLocator. */
public class ShrineLocatorTest {
    static int fails = 0, checks = 0;
    static void check(boolean ok, String what) { checks++; if (!ok) { fails++; System.out.println("FAIL: " + what); } }

    public static void main(String[] a) {
        Random rnd = new Random(42);
        int R = ShrineLocator.REGION, M = ShrineLocator.MARGIN;
        for (int s = 0; s < 40; s++) {
            long seed = rnd.nextLong();
            // 1. every region has one site inside its bounds, away from the edge, with a valid depth
            for (int rx = -6; rx <= 6; rx++) for (int rz = -6; rz <= 6; rz++) {
                var site = ShrineLocator.siteOfRegion(seed, rx, rz);
                check(site.chunkX() >= rx * R + M && site.chunkX() < (rx + 1) * R - M, "x inside region " + rx + "," + rz);
                check(site.chunkZ() >= rz * R + M && site.chunkZ() < (rz + 1) * R - M, "z inside region");
                check(site.y() >= ShrineLocator.MIN_Y && site.y() <= ShrineLocator.MAX_Y, "y range " + site.y());
                // shrine footprint is cx-12..cx+27 blocks: it must stay inside its own region (no overlap with neighbours)
                int minBlock = (site.chunkX() << 4) - 12, maxBlock = (site.chunkX() << 4) + 27;
                check(minBlock >= rx * R * 16 && maxBlock < (rx + 1) * R * 16, "footprint stays in region");
                check(ShrineLocator.siteOfRegion(seed, rx, rz).equals(site), "deterministic");
            }
            // 2. exactly one chunk per region reports a site, and it is the same one (negative coords included)
            int found = 0, wrong = 0;
            for (int cx = -2 * R; cx < 2 * R; cx++) for (int cz = -2 * R; cz < 2 * R; cz++) {
                var site = ShrineLocator.siteInChunk(seed, cx, cz);
                if (site != null) { found++; if (site.chunkX() != cx || site.chunkZ() != cz) wrong++; }
            }
            check(found == 16, "16 sites in 4x4 regions, got " + found);
            check(wrong == 0, "siteInChunk returns its own chunk");
            // 3. nearest() equals a brute-force search over a much wider area
            for (int t = 0; t < 60; t++) {
                double x = (rnd.nextDouble() - 0.5) * 6000, z = (rnd.nextDouble() - 0.5) * 6000;
                var n = ShrineLocator.nearest(seed, x, z);
                double best = Double.MAX_VALUE;
                int rx0 = Math.floorDiv((int) Math.floor(x) >> 4, R), rz0 = Math.floorDiv((int) Math.floor(z) >> 4, R);
                for (int dx = -7; dx <= 7; dx++) for (int dz = -7; dz <= 7; dz++) {
                    var q = ShrineLocator.siteOfRegion(seed, rx0 + dx, rz0 + dz);
                    best = Math.min(best, Math.hypot(q.blockX() - x, q.blockZ() - z));
                }
                check(Math.abs(Math.hypot(n.blockX() - x, n.blockZ() - z) - best) < 1e-9, "nearest is truly nearest");
                check(Math.hypot(n.blockX() - x, n.blockZ() - z) <= R * 16 * 1.5 + 1, "a shrine is always within ~290 blocks");
            }
        }
        // 4. different seeds give different worlds
        check(!ShrineLocator.siteOfRegion(1L, 0, 0).equals(ShrineLocator.siteOfRegion(2L, 0, 0))
                || !ShrineLocator.siteOfRegion(1L, 1, 0).equals(ShrineLocator.siteOfRegion(2L, 1, 0)), "seed changes layout");
        // 5. spread: sites should not all sit in the same corner of their region
        double sx = 0; int n = 0;
        for (int rx = 0; rx < 200; rx++) { sx += ShrineLocator.siteOfRegion(7L, rx, 3).chunkX() - rx * R; n++; }
        double mean = sx / n;
        check(mean > 4.5 && mean < 7.5, "x offsets are centred (mean " + mean + ")");
        System.out.println(checks + " checks, " + fails + " failures");
        System.exit(fails == 0 ? 0 : 1);
    }
}
