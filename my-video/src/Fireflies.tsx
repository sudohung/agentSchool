import { useState, useEffect, useRef } from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

type MovementType = "straight" | "random_turn" | "inward" | "outward";

interface Firefly {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color1: string;
  color2: string;
  baseBrightness: number;
  createdAt: number;
  lifetime: number;
  movementType: MovementType;
  turnSpeed: number;
  turnPhase: number;
  brightnessModifier: number;
}

const PI_DIGITS =
  "3141592653589793238462643383279502884197169399375105820974944592307816406286";

const getPiDigit = (index: number): number => {
  const digit = parseInt(PI_DIGITS[index % PI_DIGITS.length], 10);
  return digit === 0 ? 1 : digit;
};

const getRandFromPiAndTime = (
  index: number,
  absTime: number,
  min: number,
  max: number,
): number => {
  const piDigit = getPiDigit(index);
  const timeComponent = Math.sin(absTime * 0.001 + index) * 0.5 + 0.5;
  const piComponent = piDigit / 9;
  const combined = (piComponent * 0.6 + timeComponent * 0.4);
  return min + combined * (max - min);
};

const getNormalFromPiAndTime = (
  index: number,
  absTime: number,
  mean: number,
  std: number,
): number => {
  let u1 = getPiDigit((index * 7 + Math.floor(absTime * 0.001)) % PI_DIGITS.length) / 10;
  let u2 = getPiDigit((index * 13 + Math.floor(absTime * 0.0005)) % PI_DIGITS.length) / 10;
  const timeFactor = Math.sin(absTime * 0.0005 + index) * 0.3;
  while (u1 === 0) u1 = 0.1 + timeFactor;
  while (u2 === 0) u2 = 0.1 - timeFactor;

  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2 + absTime * 0.001);
  return mean + z * std;
};

const getMovementType = (index: number, time: number): MovementType => {
  const digit = getPiDigit(index + Math.floor(time * 0.1));
  const types: MovementType[] = [
    "straight",
    "random_turn",
    "inward",
    "outward",
  ];
  return types[digit % 4];
};

const getRandomColor = (index: number, time: number): string => {
  const hue1 = getRandFromPiAndTime(index * 3, time, 0, 360);
  const sat = getRandFromPiAndTime(index * 3 + 2, time, 70, 100);
  const light = getRandFromPiAndTime(index * 5, time, 50, 70);
  return `hsl(${hue1}, ${sat}%, ${light}%)`;
};

const getRandomColor2 = (index: number, time: number, hue1: number): string => {
  const hue2 = (hue1 + getRandFromPiAndTime(index * 7, time, 15, 45)) % 360;
  const sat = getRandFromPiAndTime(index * 11, time, 60, 90);
  const light = getRandFromPiAndTime(index * 13, time, 40, 60);
  return `hsl(${hue2}, ${sat}%, ${light}%)`;
};

export const Fireflies = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const [fireflies, setFireflies] = useState<Firefly[]>([]);
  const nextIdRef = useRef(0);
  const lastSpawnTimeRef = useRef(-100);
  const startTimeRef = useRef(Date.now());
  const prevPositionsRef = useRef<Map<number, { x: number; y: number; vx: number; vy: number }>>(new Map());

  const frameTime = frame / fps;
  const absTime = Date.now() - startTimeRef.current;
  const centerX = width / 2;
  const centerY = height / 2;

  useEffect(() => {
    const timeSinceLastSpawn = frameTime - lastSpawnTimeRef.current;
    const spawnInterval = getRandFromPiAndTime(nextIdRef.current * 17, absTime, 1, 5);

    if (timeSinceLastSpawn >= spawnInterval) {
      const id = nextIdRef.current++;
      const x = getNormalFromPiAndTime(id * 19, absTime, centerX, width / 6);
      const y = getNormalFromPiAndTime(id * 23, absTime, centerY, height / 5);
      const size = getRandFromPiAndTime(id * 29, absTime, 3, 8);
      const baseBrightness = getRandFromPiAndTime(id * 31, absTime, 0.4, 1);
      const lifetime = getRandFromPiAndTime(id * 37, absTime, 10, 50);
      const movementType = getMovementType(id * 41, absTime);
      const speed = getRandFromPiAndTime(id * 43, absTime, 15, 45);
      const angle = getRandFromPiAndTime(id * 47, absTime, 0, Math.PI * 2);
      const turnSpeed = getRandFromPiAndTime(id * 53, absTime, 0.3, 1.5);
      const turnPhase = getRandFromPiAndTime(id * 59, absTime, 0, Math.PI * 2);
      const brightnessModifier = getRandFromPiAndTime(id * 61, absTime, 0.3, 0.8);

      const color1 = getRandomColor(id * 67, absTime);
      const color2 = getRandomColor2(
        id * 67,
        absTime,
        parseInt(color1.match(/\d+/)?.[0] || "0", 10),
      );

      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;

      prevPositionsRef.current.set(id, { x, y, vx, vy });

      const newFirefly: Firefly = {
        id,
        x,
        y,
        vx,
        vy,
        size,
        color1,
        color2,
        baseBrightness,
        createdAt: frameTime,
        lifetime,
        movementType,
        turnSpeed,
        turnPhase,
        brightnessModifier,
      };

      setFireflies((prev) => [...prev, newFirefly]);
      lastSpawnTimeRef.current = frameTime;
    }

    setFireflies((prev) => {
      const aliveIds = new Set(prev.map(ff => ff.id));
      prevPositionsRef.current.forEach((_, id) => {
        if (!aliveIds.has(id)) {
          prevPositionsRef.current.delete(id);
        }
      });
      return prev.filter((ff) => frameTime - ff.createdAt < ff.lifetime);
    });
  }, [frame, width, height, fps, frameTime, absTime]);

  const getFireflyPosition = (ff: Firefly): { x: number; y: number; vx: number; vy: number } => {
    const age = frameTime - ff.createdAt;
    const prev = prevPositionsRef.current.get(ff.id);
    const startPos = prev || { x: ff.x, y: ff.y, vx: ff.vx, vy: ff.vy };

    let newX = startPos.x + startPos.vx * (1 / fps);
    let newY = startPos.y + startPos.vy * (1 / fps);
    let newVx = startPos.vx;
    let newVy = startPos.vy;

    if (newX - ff.size * 3 < 0) {
      newX = ff.size * 3;
      newVx = Math.abs(newVx);
    } else if (newX + ff.size * 3 > width) {
      newX = width - ff.size * 3;
      newVx = -Math.abs(newVx);
    }

    if (newY - ff.size * 3 < 0) {
      newY = ff.size * 3;
      newVy = Math.abs(newVy);
    } else if (newY + ff.size * 3 > height) {
      newY = height - ff.size * 3;
      newVy = -Math.abs(newVy);
    }

    prevPositionsRef.current.set(ff.id, { x: newX, y: newY, vx: newVx, vy: newVy });
    return { x: newX, y: newY, vx: newVx, vy: newVy };
  };

  return (
    <svg
      width="100%"
      height="100%"
      style={{
        background:
          "linear-gradient(to bottom, #0a0a1a 0%, #1a1a2e 50%, #0d0d1a 100%)",
      }}
    >
      <defs>
        {fireflies.map((ff) => (
          <radialGradient key={ff.id} id={`glow-${ff.id}`}>
            <stop
              offset="0%"
              stopColor={ff.color1}
              stopOpacity={ff.baseBrightness}
            />
            <stop
              offset="40%"
              stopColor={ff.color2}
              stopOpacity={ff.baseBrightness * 0.5}
            />
            <stop offset="100%" stopColor={ff.color2} stopOpacity="0" />
          </radialGradient>
        ))}

        <filter id="blur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" />
        </filter>
      </defs>

      {fireflies.map((ff) => {
        const age = frameTime - ff.createdAt;
        const lifeProgress = age / ff.lifetime;

        const opacity = interpolate(
          lifeProgress,
          [0, 0.1, 0.8, 1],
          [0, 1, 1, 0],
          {
            extrapolateRight: "clamp",
          },
        );

        const flicker = Math.sin(age * 4 + ff.id) * 0.15 + 0.85;
        const currentBrightness = ff.baseBrightness;

        const pos = getFireflyPosition(ff);
        const currentX = pos.x;
        const currentY = pos.y;

        const finalOpacity = opacity * currentBrightness * flicker;

        return (
          <g key={ff.id}>
            <circle
              cx={currentX}
              cy={currentY}
              r={ff.size * 3 * flicker}
              fill={`url(#glow-${ff.id})`}
              style={{ opacity: finalOpacity }}
            />
            <circle
              cx={currentX}
              cy={currentY}
              r={ff.size * 0.8}
              fill={ff.color1}
              style={{ opacity: finalOpacity }}
              filter="url(#blur)"
            />
            <circle
              cx={currentX}
              cy={currentY}
              r={ff.size * 0.4}
              fill="white"
              style={{ opacity: finalOpacity * 0.9 }}
            />
          </g>
        );
      })}

      <text x={20} y={30} fill="white" fontSize={14} opacity={0.6}>
        萤火虫数量: {fireflies.length} | 时间: {frameTime.toFixed(1)}s
      </text>

      <text x={20} y={55} fill="white" fontSize={12} opacity={0.4}>
        rand = f(π, 时间) | 速度3倍 | 碰撞反弹 | 亮度随移动变化
      </text>
    </svg>
  );
};
