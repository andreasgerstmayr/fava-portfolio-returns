import { useTheme } from "@mui/material";
import { RefObject, useEffect, useState } from "react";

/// A hook to get the component width of a Ref to a `HTMLElement`.
export function useComponentWidthOf(ref: RefObject<HTMLElement>) {
  // The state.
  const [parentWidth, setParentWidth] = useState(0);
  useEffect(() => {
    // If the ref is null, we do nothing
    if (ref.current) {
      // Create the observer
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          setParentWidth(entry.contentRect.width);
        }
      });

      // Initialize
      resizeObserver.observe(ref.current);

      // Disconnect the observer on disconnect
      return () => resizeObserver.disconnect();
    }
  }, [ref]);
  return parentWidth;
}

/**
 * A hook to get profit and loss colors based on the current theme.
 *
 * This hook retrieves color values from the theme and provides both solid colors and trend
 * colors with customizable opacity.
 *
 * @returns An object containing colors for representing financial profit-loss
 */
export function usePnLColors() {
  const theme = useTheme();
  const {profit, loss, lossTrend ,profitTrend} = theme["pnl-colors"]

  return {
    profit,
    loss,
    profitTrend(opacity = 1) {
      return `hsla(${profitTrend}, ${opacity})`;
    },
    lossTrend(opacity = 1) {
      return `hsla(${lossTrend}, ${opacity})`;
    },
  };
}
