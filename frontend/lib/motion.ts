import type { Variants } from "framer-motion";

export const pageVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

export const cardVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: "easeOut" },
  },
};

export const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.04 },
  },
};

export const tableRowVariants: Variants = {
  hidden: { opacity: 0, x: -4 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.2, ease: "easeOut" },
  },
};
