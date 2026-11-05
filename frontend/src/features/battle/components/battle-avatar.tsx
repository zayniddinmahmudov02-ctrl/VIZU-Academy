"use client";

import { useId } from "react";

import { cn } from "@/lib/utils";

/**
 * Battle avatars: layered SVG busts with volumetric gradients, rim light and a holographic pedestal,
 * tilted / floated with CSS 3D (no WebGL, so they stay sharp and cheap on phones).
 */

type HairStyle = "short" | "long" | "curly" | "receding" | "bun";
type Gear = "straps" | "cap" | "glasses" | "fedora" | "beard" | "medal" | "crown" | "visor";

interface Look {
  skin: string;
  skinShade: string;
  hair: string;
  hairStyle: HairStyle;
  outfit: [string, string];
  trim: string;
  gear: Gear[];
}

const LOOKS: Record<string, Look> = {
  student: { skin: "#f1c7a3", skinShade: "#d9a27c", hair: "#5b3a24", hairStyle: "short", outfit: ["#4f97f5", "#1f4e9a"], trim: "#ffffff", gear: ["straps"] },
  explorer: { skin: "#d9a07a", skinShade: "#b97d58", hair: "#2b1d14", hairStyle: "long", outfit: ["#2fb4a0", "#156b63"], trim: "#d83b43", gear: ["cap"] },
  scholar: { skin: "#f5d2b4", skinShade: "#dcae8a", hair: "#c9852c", hairStyle: "bun", outfit: ["#24406e", "#101d35"], trim: "#f2c45b", gear: ["glasses"] },
  adventurer: { skin: "#c68960", skinShade: "#a26842", hair: "#1c1410", hairStyle: "curly", outfit: ["#8a5a35", "#4b2e1a"], trim: "#f2c45b", gear: ["fedora"] },
  professor: { skin: "#eec4a0", skinShade: "#d1a07a", hair: "#c9ced8", hairStyle: "receding", outfit: ["#6b7283", "#3a4050"], trim: "#d83b43", gear: ["glasses", "beard"] },
  champion: { skin: "#a8714d", skinShade: "#87553a", hair: "#120c08", hairStyle: "short", outfit: ["#e0474f", "#8e1c23"], trim: "#f2c45b", gear: ["medal"] },
  legend: { skin: "#f0c9a6", skinShade: "#d49f7b", hair: "#f5e6c4", hairStyle: "long", outfit: ["#2a2f45", "#0b0f1d"], trim: "#f2c45b", gear: ["crown", "medal"] },
  bot: { skin: "#c9d6ea", skinShade: "#8ea3c3", hair: "#3984e8", hairStyle: "short", outfit: ["#3a4a66", "#172a46"], trim: "#3984e8", gear: ["visor"] },
};

export const AVATAR_KEYS = ["student", "explorer", "scholar", "adventurer", "professor", "champion", "legend"] as const;

function Hair({ style, color }: { style: HairStyle; color: string }) {
  switch (style) {
    case "long":
      return <path d="M58 112 C50 62 80 44 104 48 C134 52 150 76 142 116 L140 150 C134 112 128 82 104 76 C86 76 72 88 68 150 Z" fill={color} />;
    case "curly":
      return (
        <g fill={color}>
          {[[70, 74, 15], [86, 62, 16], [104, 58, 17], [122, 64, 16], [136, 78, 14], [64, 92, 11], [140, 96, 10]].map(([x, y, r]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r={r} />
          ))}
        </g>
      );
    case "receding":
      return <path d="M62 100 C60 80 66 70 74 66 C70 80 70 90 72 98 Z M138 100 C140 80 134 70 126 66 C130 80 130 90 128 98 Z M80 62 C92 56 110 56 122 62 C112 60 92 60 80 62 Z" fill={color} />;
    case "bun":
      return (
        <g fill={color}>
          <circle cx="100" cy="46" r="15" />
          <path d="M60 100 C56 64 80 52 102 52 C126 52 146 66 140 102 C134 82 120 72 100 72 C82 72 68 82 60 100 Z" />
        </g>
      );
    default:
      return <path d="M61 98 C58 62 82 50 102 51 C127 52 144 68 139 99 C133 80 118 71 100 71 C83 71 69 80 61 98 Z" fill={color} />;
  }
}

export default function BattleAvatar({
  avatar,
  size = 160,
  accent = "#3984E8",
  animated = true,
  className,
  title,
  portrait = false,
}: {
  avatar: string;
  size?: number;
  accent?: string;
  animated?: boolean;
  className?: string;
  title?: string;
  /** head-and-shoulders crop for small round frames (no pedestal, no animation) */
  portrait?: boolean;
}) {
  const look = LOOKS[avatar] ?? LOOKS.student;
  const id = useId().replace(/:/g, "");
  const has = (g: Gear) => look.gear.includes(g);
  const robot = has("visor");

  return (
    <div className={cn("relative inline-block", !portrait && "bt-avatar-tilt", className)} style={{ width: size, height: portrait ? size : size * 1.1 }} role="img" aria-label={title ?? avatar}>
      <svg viewBox={portrait ? "40 24 120 120" : "0 0 200 220"} width="100%" height="100%" className={animated && !portrait ? "bt-avatar" : undefined} aria-hidden="true">
        <defs>
          <radialGradient id={`skin${id}`} cx="38%" cy="32%" r="75%">
            <stop offset="0%" stopColor={look.skin} />
            <stop offset="55%" stopColor={look.skin} />
            <stop offset="100%" stopColor={look.skinShade} />
          </radialGradient>
          <linearGradient id={`fit${id}`} x1="0" y1="0" x2="0.4" y2="1">
            <stop offset="0%" stopColor={look.outfit[0]} />
            <stop offset="100%" stopColor={look.outfit[1]} />
          </linearGradient>
          <radialGradient id={`glow${id}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={accent} stopOpacity="0.85" />
            <stop offset="100%" stopColor={accent} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={`gold${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fff2c4" />
            <stop offset="50%" stopColor="#f2c45b" />
            <stop offset="100%" stopColor="#b97f18" />
          </linearGradient>
        </defs>

        {/* holographic pedestal */}
        {!portrait && <ellipse cx="100" cy="206" rx="86" ry="16" fill={`url(#glow${id})`} />}
        {!portrait && <ellipse cx="100" cy="206" rx="64" ry="9" fill="none" stroke={accent} strokeOpacity="0.8" strokeWidth="2" />}

        {/* shoulders */}
        <path d="M26 214 C26 168 58 146 100 146 C142 146 174 168 174 214 Z" fill={`url(#fit${id})`} />
        <path d="M26 214 C26 168 58 146 100 146" fill="none" stroke="#fff" strokeOpacity="0.18" strokeWidth="3" />
        <path d="M78 150 L100 178 L122 150" fill="none" stroke={look.trim} strokeWidth="5" strokeLinejoin="round" />
        {has("straps") && (
          <g stroke="#14294a" strokeWidth="9" strokeLinecap="round">
            <path d="M56 160 L66 214" />
            <path d="M144 160 L134 214" />
          </g>
        )}

        {/* neck + head */}
        <path d="M86 124 L86 152 C92 158 108 158 114 152 L114 124 Z" fill={look.skinShade} />
        {robot ? (
          <g>
            <rect x="58" y="52" width="84" height="84" rx="26" fill={`url(#skin${id})`} />
            <rect x="66" y="80" width="68" height="26" rx="13" fill="#0b1830" />
            <rect x="72" y="86" width="56" height="14" rx="7" fill={accent} opacity="0.9" />
            <circle cx="86" cy="93" r="4" fill="#fff" />
            <circle cx="114" cy="93" r="4" fill="#fff" />
            <line x1="100" y1="52" x2="100" y2="34" stroke="#8ea3c3" strokeWidth="4" />
            <circle cx="100" cy="30" r="6" fill={accent} />
            <path d="M84 118 Q100 126 116 118" fill="none" stroke="#0b1830" strokeWidth="4" strokeLinecap="round" />
          </g>
        ) : (
          <g>
            <ellipse cx="62" cy="102" rx="7" ry="10" fill={look.skinShade} />
            <ellipse cx="138" cy="102" rx="7" ry="10" fill={look.skinShade} />
            <ellipse cx="100" cy="98" rx="38" ry="43" fill={`url(#skin${id})`} />
            <ellipse cx="86" cy="80" rx="16" ry="12" fill="#fff" opacity="0.18" />
            <Hair style={look.hairStyle} color={look.hair} />
            {/* face */}
            <path d="M80 88 Q88 84 95 88" stroke="#3a2a20" strokeWidth="3" fill="none" strokeLinecap="round" />
            <path d="M105 88 Q112 84 120 88" stroke="#3a2a20" strokeWidth="3" fill="none" strokeLinecap="round" />
            <ellipse cx="88" cy="99" rx="4.5" ry="5.5" fill="#1b2438" />
            <ellipse cx="112" cy="99" rx="4.5" ry="5.5" fill="#1b2438" />
            <circle cx="89.5" cy="97" r="1.6" fill="#fff" />
            <circle cx="113.5" cy="97" r="1.6" fill="#fff" />
            <ellipse cx="80" cy="114" rx="6" ry="3.5" fill="#e88a7a" opacity="0.25" />
            <ellipse cx="120" cy="114" rx="6" ry="3.5" fill="#e88a7a" opacity="0.25" />
            <path d="M89 120 Q100 128 111 120" fill="none" stroke="#7a3b30" strokeWidth="3" strokeLinecap="round" />
            {has("beard") && <path d="M70 110 C72 140 88 148 100 148 C112 148 128 140 130 110 C124 126 112 132 100 132 C88 132 76 126 70 110 Z" fill={look.hair} />}
            {has("glasses") && (
              <g fill="none" stroke="#1b2438" strokeWidth="2.6">
                <circle cx="88" cy="99" r="11" />
                <circle cx="112" cy="99" r="11" />
                <path d="M99 99 L101 99 M77 97 L66 94 M123 97 L134 94" />
              </g>
            )}
            {/* rim light */}
            <path d="M126 70 C140 84 142 108 130 128" fill="none" stroke="#fff" strokeOpacity="0.35" strokeWidth="3" strokeLinecap="round" />
          </g>
        )}

        {has("cap") && (
          <g>
            <path d="M60 84 C60 54 84 44 102 44 C122 44 142 56 142 84 Z" fill="#172a46" />
            <path d="M120 80 C138 78 156 82 166 90 C150 92 132 90 120 88 Z" fill="#0f1c33" />
            <rect x="60" y="78" width="82" height="7" rx="3.5" fill={look.trim} />
          </g>
        )}
        {has("fedora") && (
          <g>
            <ellipse cx="100" cy="72" rx="62" ry="12" fill="#3b2616" />
            <path d="M68 72 C68 44 84 36 100 36 C116 36 132 44 132 72 Z" fill="#4e321d" />
            <rect x="68" y="62" width="64" height="7" fill={look.trim} />
          </g>
        )}
        {has("crown") && (
          <g>
            <path d="M68 58 L74 34 L88 50 L100 28 L112 50 L126 34 L132 58 Z" fill={`url(#gold${id})`} stroke="#8a5d10" strokeWidth="1.5" />
            <circle cx="100" cy="46" r="4" fill="#d83b43" />
          </g>
        )}
        {has("medal") && (
          <g>
            <path d="M88 150 L96 182 M112 150 L104 182" stroke="#d83b43" strokeWidth="6" />
            <circle cx="100" cy="190" r="12" fill={`url(#gold${id})`} stroke="#8a5d10" strokeWidth="1.5" />
            <path d="M100 183 L102.5 188 L108 188.5 L104 192 L105 197.5 L100 194.8 L95 197.5 L96 192 L92 188.5 L97.5 188 Z" fill="#fff6d8" />
          </g>
        )}
      </svg>
    </div>
  );
}
