import { motion } from 'framer-motion';

export default function LoaderDots() {
  const variant = {
    animate: {
      opacity: [0.2, 1, 0.2],
      transition: { repeat: Infinity, duration: 1 }
    }
  };
  return (
    <div className="flex gap-1">
      {Array.from({ length: 3 }).map((_, i) => (
        <motion.span
          key={i}
          className="h-2 w-2 rounded-full bg-muted-foreground"
          variants={variant}
          animate="animate"
        />
      ))}
    </div>
  );
}
