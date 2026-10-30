package com.hagoyama;

import com.mojang.brigadier.CommandDispatcher;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.ComponentUtils;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** /hagoyama locate (everyone) and the op-only test helpers /hagoyama trance | awaken | reset */
@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID)
public final class HagoyamaCommands {
    private HagoyamaCommands() { }

    @SubscribeEvent
    public static void register(RegisterCommandsEvent e) {
        CommandDispatcher<CommandSourceStack> d = e.getDispatcher();
        d.register(Commands.literal("hagoyama")
                .then(Commands.literal("locate").executes(c -> locate(c.getSource())))
                .then(Commands.literal("trance").requires(s -> s.hasPermission(2)).executes(c -> {
                    Trance.enter(c.getSource().getPlayerOrException());
                    return 1;
                }))
                .then(Commands.literal("awaken").requires(s -> s.hasPermission(2)).executes(c -> {
                    ServerPlayer p = c.getSource().getPlayerOrException();
                    Trance.data(p).putBoolean(Trance.K_AWAKE, true);
                    c.getSource().sendSuccess(() -> Component.literal("Hagoyama awakened."), false);
                    return 1;
                }))
                .then(Commands.literal("reset").requires(s -> s.hasPermission(2)).executes(c -> {
                    ServerPlayer p = c.getSource().getPlayerOrException();
                    Trance.data(p).remove(Trance.K_AWAKE);
                    Trance.data(p).remove(Trance.K_CLAIMED);
                    Inventory inv = p.getInventory();
                    for (int i = 0; i < inv.getContainerSize(); i++) {
                        ItemStack s = inv.getItem(i);
                        if (s.getItem() instanceof HagoyamaSwordItem && s.hasTag()) s.getTag().remove(HagoyamaSwordItem.TAG_AWAKE);
                    }
                    c.getSource().sendSuccess(() -> Component.literal("Hagoyama progress reset."), false);
                    return 1;
                })));
    }

    /** Points at the nearest cave shrine (the place where Hagoyama waits). Works in unexplored terrain too. */
    private static int locate(CommandSourceStack src) {
        ServerLevel lv = src.getLevel();
        if (lv.dimension() != Level.OVERWORLD) {
            src.sendFailure(Component.literal("The Hagoyama cave shrine only exists in the Overworld."));
            return 0;
        }
        Vec3 pos = src.getPosition();
        ShrineLocator.Site site = ShrineLocator.nearest(lv.getSeed(), pos.x, pos.z);
        int x = site.blockX();
        int y = site.y();
        int z = site.blockZ();
        int dist = (int) Math.round(Math.hypot(x - pos.x, z - pos.z));
        Component coords = ComponentUtils.wrapInSquareBrackets(Component.literal(x + ", " + y + ", " + z))
                .withStyle(st -> st.withColor(ChatFormatting.GREEN)
                        .withClickEvent(new ClickEvent(ClickEvent.Action.SUGGEST_COMMAND, "/tp @s " + x + " " + y + " " + z))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal("Click to get a /tp command"))));
        src.sendSuccess(() -> Component.literal("Nearest Hagoyama cave shrine: ").append(coords)
                .append(Component.literal(" - " + dist + " blocks away. Dig down to about Y " + y + ".")), false);
        return dist;
    }
}
