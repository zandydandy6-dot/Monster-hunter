package com.hagoyama;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

public class HagoyamaSwordItem extends SwordItem {
    public static final String TAG_MOVE = "HagoyamaMove";
    public static final String TAG_AWAKE = "HagoyamaAwake";

    private static final Tier TIER = new Tier() {
        @Override public int getUses() { return 3000; }
        @Override public float getSpeed() { return 9.0F; }
        @Override public float getAttackDamageBonus() { return 4.0F; }
        @Override public int getLevel() { return 4; }
        @Override public int getEnchantmentValue() { return 20; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.NETHERITE_INGOT); }
    };

    public HagoyamaSwordItem(Item.Properties props) {
        super(TIER, 2, -2.2F, props);
    }

    public static boolean isAwake(ItemStack s) {
        return s.hasTag() && s.getTag().getBoolean(TAG_AWAKE);
    }

    public static Moves getMove(ItemStack s) {
        return Moves.get(s.hasTag() ? s.getTag().getInt(TAG_MOVE) : 0);
    }

    /** Server side: called when the player presses the switch-move key. */
    public static void switchMove(ServerPlayer p) {
        ItemStack s = p.getMainHandItem();
        if (!(s.getItem() instanceof HagoyamaSwordItem)) return;
        if (!isAwake(s)) {
            p.displayClientMessage(Component.literal("The blade's eyes are still closed.")
                    .withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC), true);
            return;
        }
        s.getOrCreateTag().putInt(TAG_MOVE, Math.floorMod(s.getOrCreateTag().getInt(TAG_MOVE) + 1, Moves.values().length));
        p.displayClientMessage(Component.literal("Move: ").withStyle(ChatFormatting.GRAY)
                .append(Component.literal(getMove(s).display).withStyle(ChatFormatting.AQUA)), true);
        p.level().playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.8F, 1.2F);
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (!level.isClientSide && entity instanceof Player p && !isAwake(stack) && Trance.data(p).getBoolean(Trance.K_AWAKE)) {
            stack.getOrCreateTag().putBoolean(TAG_AWAKE, true);
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return isAwake(stack) || super.isFoil(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tip, TooltipFlag flag) {
        if (isAwake(stack)) {
            Moves m = getMove(stack);
            tip.add(Component.literal("Move: " + m.display).withStyle(ChatFormatting.AQUA));
            tip.add(Component.literal(m.description).withStyle(ChatFormatting.DARK_GRAY));
        } else {
            tip.add(Component.literal("Its eyes are still closed.").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
        }
    }
}
