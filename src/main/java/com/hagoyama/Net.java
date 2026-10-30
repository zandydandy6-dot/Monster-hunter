package com.hagoyama;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

public final class Net {
    private static final String VERSION = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(HagoyamaMod.MODID, "main"), () -> VERSION, VERSION::equals, VERSION::equals);

    /** Client -> server: cycle to the next move. */
    public static class SwitchMove { }

    /** Server -> client: show the fading reflection. */
    public static class Reflection {
        public final int ticks;
        public Reflection(int ticks) { this.ticks = ticks; }
    }

    public static void register() {
        int id = 0;
        CHANNEL.registerMessage(id++, SwitchMove.class, (m, b) -> { }, b -> new SwitchMove(), Net::handleSwitch);
        CHANNEL.registerMessage(id++, Reflection.class, (m, b) -> b.writeVarInt(m.ticks),
                b -> new Reflection(b.readVarInt()), Net::handleReflection);
    }

    public static void sendReflection(ServerPlayer p, int ticks) {
        CHANNEL.send(PacketDistributor.PLAYER.with(() -> p), new Reflection(ticks));
    }

    private static void handleSwitch(SwitchMove m, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> {
            ServerPlayer p = ctx.get().getSender();
            if (p != null) HagoyamaSwordItem.switchMove(p);
        });
        ctx.get().setPacketHandled(true);
    }

    private static void handleReflection(Reflection m, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn(Dist.CLIENT,
                () -> () -> com.hagoyama.client.ClientEvents.startReflection(m.ticks)));
        ctx.get().setPacketHandled(true);
    }
}
