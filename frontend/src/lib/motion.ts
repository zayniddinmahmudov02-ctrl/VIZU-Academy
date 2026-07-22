import type { Transition, Variants } from "framer-motion";

/** Standard easing/duration used across the app — keep every animated
 *  surface on the same rhythm instead of hand-tuning per component. */
export const easeOut: Transition = { duration: 0.25, ease: "easeOut" };
export const easeOutSlow: Transition = { duration: 0.3, ease: "easeOut" };

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: easeOut },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: easeOut },
};

/** Stagger a list of children (cards, stat tiles, nav items). */
export const staggerContainer: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06, delayChildren: 0.04 },
  },
};

export const cardEntrance: Variants = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: easeOut },
};

/** Hover/tap affordance for interactive cards. */
export const scaleOnHover = {
  whileHover: { scale: 1.02, transition: easeOut },
  whileTap: { scale: 0.98, transition: { duration: 0.15 } },
};

export const pageTransition: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: easeOut },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15, ease: "easeIn" } },
};
