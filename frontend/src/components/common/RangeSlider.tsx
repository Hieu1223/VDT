import React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import "@/components/common/RangeSlider.css";

interface Props {
  min: number;
  max: number;
  step?: number;
  value: number[];
  onValueChange: (value: number[]) => void;
  testId?: string;
}

/** A single track with one or two draggable thumbs (pass a 1-value array for
 * a plain slider, or a 2-value array for a true min/max range slider). */
export function RangeSlider({ min, max, step = 1, value, onValueChange, testId }: Props) {
  return (
    <SliderPrimitive.Root
      className="range-slider-root"
      min={min}
      max={max}
      step={step}
      value={value}
      onValueChange={onValueChange}
      minStepsBetweenThumbs={value.length > 1 ? 1 : 0}
      data-testid={testId}
    >
      <SliderPrimitive.Track className="range-slider-track">
        <SliderPrimitive.Range className="range-slider-range" />
      </SliderPrimitive.Track>
      {value.map((_, i) => (
        <SliderPrimitive.Thumb key={i} className="range-slider-thumb" data-testid={testId ? `${testId}-thumb-${i}` : undefined} />
      ))}
    </SliderPrimitive.Root>
  );
}
