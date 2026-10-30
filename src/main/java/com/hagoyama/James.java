package com.hagoyama;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevelAccessor;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.Animation;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * James - the blue-haired wielder: calm until hit, then fights back with the black Hagoyama sword.
 * Animated with GeckoLib (idle, walk and three different sword slashes). Killing him drops one piece of his clothes.
 */
public class James extends Monster implements GeoEntity {
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("animation.james.idle");
    private static final RawAnimation WALK = RawAnimation.begin().thenLoop("animation.james.walk");
    private static final String[] SLASHES = {"animation.james.slash_1", "animation.james.slash_2", "animation.james.slash_3"};

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int slashIndex; // client side only: which slash plays next

    public James(EntityType<? extends James> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected boolean shouldDespawnInPeaceful() {
        return false; // he is not a monster-style threat, so peaceful mode keeps him
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.1, false));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance diff, MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, diff, reason, data, tag);
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(HagoyamaMod.HAGOYAMA.get()));
        setPersistenceRequired();
        setDropChance(EquipmentSlot.MAINHAND, 0.0F); // the sword stays a cave-only reward
        return result;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "move", 5,
                state -> state.setAndContinue(state.isMoving() ? WALK : IDLE)));
        // Registered last so a slash wins over the walk cycle on the arms while it plays.
        controllers.add(new AnimationController<>(this, "attack", 2, state -> {
            if (this.swinging && state.getController().getAnimationState() == AnimationController.State.STOPPED) {
                state.getController().forceAnimationReset();
                state.getController().setAnimation(RawAnimation.begin()
                        .then(SLASHES[slashIndex++ % SLASHES.length], Animation.LoopType.PLAY_ONCE));
                this.swinging = false;
            }
            return PlayState.CONTINUE;
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
