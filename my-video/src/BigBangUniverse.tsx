import { useMemo, useCallback } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

// =====================================================
// 物理常数与参数3
// =====================================================
const PHYSICAL_CONSTANTS = {
  PLANCK_TIME: 5.39e-44,
  PLANCK_TEMPERATURE: 1.416e32,
  PLANCK_LENGTH: 1.616e-35,
  PLANCK_MASS: 2.176e-8,
  INFLATION_FACTOR: 1e26,
  CMB_TEMPERATURE: 2.725,
  CMB_DECOUPLING_TEMP: 3000,
  NUCLEOSYNTHESIS_TEMP: 1e9,
  QUARK_CONFINEMENT_TEMP: 1e12,
  ELECTROWEAK_TEMP: 1e15,
  GUT_TEMP: 1e28,
  UNIVERSE_AGE: 13.8e9,
  LIGHT_SPEED: 299792458,
  BARYON_DENSITY: 0.0224,
  DARK_MATTER_DENSITY: 0.12,
  DARK_ENERGY_DENSITY: 0.684,
  HUBBLE_CONSTANT: 67.4,
};

// =====================================================
// 时期定义（对数时间轴）
// =====================================================
interface CosmicEpoch {
  name: string;
  nameEn: string;
  startTime: number; // 秒
  endTime: number; // 秒
  startFrame: number;
  endFrame: number;
  temperature: number; // K
  description: string;
  color: string;
}

const EPOCHS: CosmicEpoch[] = [
  {
    name: "普朗克时期",
    nameEn: "Planck Epoch",
    startTime: 0,
    endTime: 1e-43,
    startFrame: 0,
    endFrame: 10,
    temperature: 1e32,
    description: "量子引力主导，四种力统一",
    color: "#FFFFFF",
  },
  {
    name: "大一统时期",
    nameEn: "GUT Epoch",
    startTime: 1e-43,
    endTime: 1e-36,
    startFrame: 10,
    endFrame: 20,
    temperature: 1e28,
    description: "重力分离，GUT对称性",
    color: "#EEDDFF",
  },
  {
    name: "暴胀时期",
    nameEn: "Inflation",
    startTime: 1e-36,
    endTime: 1e-32,
    startFrame: 20,
    endFrame: 40,
    temperature: 1e27,
    description: "指数膨胀10²⁶倍",
    color: "#FFDDAA",
  },
  {
    name: "再加热",
    nameEn: "Reheating",
    startTime: 1e-32,
    endTime: 1e-12,
    startFrame: 40,
    endFrame: 60,
    temperature: 1e15,
    description: "暴胀场衰变，粒子产生",
    color: "#FFAA66",
  },
  {
    name: "电弱时期",
    nameEn: "Electroweak",
    startTime: 1e-12,
    endTime: 1e-6,
    startFrame: 60,
    endFrame: 80,
    temperature: 1e15,
    description: "电磁力与弱力分离",
    color: "#FF8844",
  },
  {
    name: "夸克时期",
    nameEn: "Quark Epoch",
    startTime: 1e-6,
    endTime: 1e-4,
    startFrame: 80,
    endFrame: 100,
    temperature: 1e12,
    description: "夸克-胶子等离子体",
    color: "#FF6622",
  },
  {
    name: "强子时期",
    nameEn: "Hadron Epoch",
    startTime: 1e-4,
    endTime: 1,
    startFrame: 100,
    endFrame: 120,
    temperature: 1e10,
    description: "质子中子形成",
    color: "#CC4400",
  },
  {
    name: "轻子时期",
    nameEn: "Lepton Epoch",
    startTime: 1,
    endTime: 180,
    startFrame: 120,
    endFrame: 140,
    temperature: 1e9,
    description: "轻子主导宇宙",
    color: "#AA3300",
  },
  {
    name: "核合成",
    nameEn: "Nucleosynthesis",
    startTime: 180,
    endTime: 1200,
    startFrame: 140,
    endFrame: 160,
    temperature: 1e9,
    description: "氢、氦、锂形成",
    color: "#882200",
  },
  {
    name: "光子时期",
    nameEn: "Photon Epoch",
    startTime: 1200,
    endTime: 3.8e5 * 365.25 * 24 * 3600,
    startFrame: 160,
    endFrame: 200,
    temperature: 3000,
    description: "等离子体不透明",
    color: "#441100",
  },
  {
    name: "复合时期",
    nameEn: "Recombination",
    startTime: 3.8e5 * 365.25 * 24 * 3600,
    endTime: 1e6 * 365.25 * 24 * 3600,
    startFrame: 200,
    endFrame: 220,
    temperature: 3000,
    description: "CMB释放，中性原子形成",
    color: "#220800",
  },
  {
    name: "黑暗时期",
    nameEn: "Dark Ages",
    startTime: 1e6 * 365.25 * 24 * 3600,
    endTime: 1.5e8 * 365.25 * 24 * 3600,
    startFrame: 220,
    endFrame: 250,
    temperature: 100,
    description: "无恒星，只有中性氢",
    color: "#110400",
  },
  {
    name: "再电离",
    nameEn: "Reionization",
    startTime: 1.5e8 * 365.25 * 24 * 3600,
    endTime: 1e9 * 365.25 * 24 * 3600,
    startFrame: 250,
    endFrame: 280,
    temperature: 50,
    description: "第一代恒星形成",
    color: "#0A0200",
  },
  {
    name: "星系形成",
    nameEn: "Galaxy Formation",
    startTime: 1e9 * 365.25 * 24 * 3600,
    endTime: 13.8e9 * 365.25 * 24 * 3600,
    startFrame: 280,
    endFrame: 600,
    temperature: 2.725,
    description: "大尺度结构演化",
    color: "#000001",
  },
];

// =====================================================
// 工具函数
// =====================================================
const PI_DIGITS =
  "31415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679821480865132823066470938446095505822317253594081284811174502841027019385211055596446229489549303819644288109756659334461284756482337867831652712019091456485669234603486104543266482133936072602491412737245870066063155881748815209209628292540917153643678925903600113305305488204665213841469519415116094330572703657595919530921861173819326117931051185480744623799627495673518857527248912279381830119491298336733624406566430860213949463952247371907021798609437027705392171762931767523846748184676694051320005681271452635608277857713427577896091736371787214684409012249534301465495853710507922796892589235420199561121290219608640344181598136297747713099605187072113499999983729780499510597317328160963185950244594553469083026425223082533446850352619311881710100031378387528865875332083814206171776691473035982534904287554687311595628638823537875937519577818577805321712268066130019278766111959092164201989380952572010654858632788659361533818279682303019520353018529689957736225994138912497217752834791315155748572424541506959508295331168617278558890750983817546374649393192550604009277016711390098488240128583616035637076601047101819429555961989467678374494482553797747268471040475346462080466842590694912933136770289891521047521620569660240580381501935112533824300355876402474964732639141992726042699227967823547816360093417216412199245863150302861829745557067498385054945885869269956909250520091388377238363169283197911837547241727901598882728417241575684805090951801918117188393567625326534639647005349963220749276689740825216244596469078617778043289899651675960892351588647766817891289646076123443568635818348495415663114941565275793430583426665014443626452160606961041627808527790057569609319448529360817662025121125185653766905139182136813951760546191608416728544506973782725114123239113180445458147890557166274857989189411973826894676543508829652309837783381563590785020587853795143056018378547250495569691830627948421162060482353567740110895349530824409690587925252675727242333495500331003380224535203858531835653211668388286732356495641832244866444012666044237682067853651045648795012445338759837372988374826067217868933554429448136856300986201245961897839226125978723434145412359028586912023298562403106194621730205264894803244026502882455361524619115738105491089351899700423317580399145398716652838260552053864486655367682733244094135867918420963318862310211720775048051655163255272328919956363740814964054495407624345833096935618848658786512482542353597038743844867235637350209098873893407426401491845766833770248739595700020651514091310693588417747882790998935678733743047155464890976001162080982342739309310373139883219975924333395810383848345103438339668398889769164348327182731036185133618982572130968067549601165563851561021396586311632616378596328459536594454426866968353831956589921341396727689224524365613976507492639165379829701162507825114998105264986919358741768635198589919457947202287827824376204308407774233820538814985841301360914735884537378778248302958777843310148412659307213611560471945190297726632969163295260660624300352138496956664924453033245477905398950600780057705355450897800345869358645620370049642049678246280429211531931363862000132802769601404681178202190821404069458190189301839977870303618325384504724188046337267101456523864644839188060470418136132030236175625265513025484586959408770755472439500245832093566125235759598248250886832642840655744692306053744499133944214111026805090045122928329497333784527239793935404835382490773184774826522243669415782431020326844326142985913867796020027428914036621753604426752116818124267143286059855539541747793265173724730268288306765666766850000072702198257977867404005298768954321780479424816642233644847360625898281880043325790340284140392733761845673476330366713560822526481417852671900969966942523271082374981580900834912754892378966776309164132481354323236367688576545504080699168177221688431934215130837180255165808303180155471038552265323961525882056799917269894173899051734758406916748006962606696497976568404016234903307847672518071161046831030249825568058322503773047426833546219489045570308038805093893204937293259419828911090781683423525926950775085699992571184978278967903027962124873401640897083512530519165473608726895594146044901762354509336900694907490835356059019952609530253729848557135032533943049481940229220649095275736234586315783834914601093126517002890068832710475227129573876684210882883334903949169475805415784126726611696630824522950604855651788689854231489396920742009245713124676384404328649571935143525039093840084932031962535179128832104412901401125893906209924389101158731928170230458261841295046313433205053426246904689500057758428233980285281930206369873791679334430200976405384055835969193172916066054929703";

const getPiDigit = (index: number): number => {
  return parseInt(PI_DIGITS[index % PI_DIGITS.length], 10) || 1;
};

const getPiRandom = (index: number, min: number, max: number): number => {
  const digit = getPiDigit(index);
  return min + (digit / 9) * (max - min);
};

// 温度转颜色（黑体辐射）
const tempToColor = (temp: number): string => {
  if (temp > 1e7) return "#BBDDFF"; // >10MK: 蓝白
  if (temp > 1e6) return "#DDEEFF"; // 1-10MK: 白
  if (temp > 1e5) return "#FFFFDD"; // 100K-1MK: 黄白
  if (temp > 1e4) return "#FFDD88"; // 10K-100K: 黄
  if (temp > 5000) return "#FFAA44"; // 5K-10K: 橙黄
  if (temp > 3000) return "#FF8822"; // 3K-5K: 橙
  if (temp > 1000) return "#CC4400"; // 1K-3K: 红橙
  if (temp > 100) return "#662200"; // 100-1K: 暗红
  return "#110500"; // <100K: 近黑
};

// 格式化时间
const formatTime = (seconds: number): string => {
  if (seconds < 1e-36) return `${(seconds / 1e-43).toFixed(1)} tₚ`;
  if (seconds < 1e-30) return `${(seconds * 1e30).toFixed(1)}×10⁻³⁰ s`;
  if (seconds < 1e-20) return `${(seconds * 1e20).toFixed(1)}×10⁻²⁰ s`;
  if (seconds < 1e-10) return `${(seconds * 1e12).toFixed(1)} ps`;
  if (seconds < 1e-6) return `${(seconds * 1e9).toFixed(1)} ns`;
  if (seconds < 1e-3) return `${(seconds * 1e6).toFixed(1)} μs`;
  if (seconds < 1) return `${(seconds * 1e3).toFixed(1)} ms`;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)} min`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)} hr`;
  if (seconds < 3.15e7) return `${(seconds / 86400).toFixed(1)} days`;
  if (seconds < 3.15e9) return `${(seconds / 3.15e7).toFixed(1)} years`;
  if (seconds < 3.15e13) return `${(seconds / 3.15e9).toFixed(1)} kyr`;
  return `${(seconds / 3.15e7 / 1e9).toFixed(2)} Gyr`;
};

// 缓动函数
const smoothstep = (edge0: number, edge1: number, x: number): number => {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
};

// =====================================================
// 物理计算
// =====================================================
const getPhysicalTime = (frame: number): number => {
  for (const epoch of EPOCHS) {
    if (frame >= epoch.startFrame && frame < epoch.endFrame) {
      const progress =
        (frame - epoch.startFrame) / (epoch.endFrame - epoch.startFrame);
      const logStart = Math.log10(epoch.startTime || 1e-50);
      const logEnd = Math.log10(epoch.endTime);
      const logTime = logStart + progress * (logEnd - logStart);
      return Math.pow(10, logTime);
    }
  }
  return EPOCHS[EPOCHS.length - 1].endTime;
};

const getTemperature = (time: number): number => {
  if (time < 1e-32) return PHYSICAL_CONSTANTS.PLANCK_TEMPERATURE;
  // 辐射主导: T ∝ t^(-1/2)
  if (time < 1e12) return 1e10 * Math.pow(time, -0.5);
  // 物质主导: T ∝ t^(-2/3)
  return 1e4 * Math.pow(time / 1e12, -0.67);
};

const getScaleFactor = (time: number): number => {
  if (time < 1e-32) return Math.pow(time / 1e-43, 0.5);
  if (time < 1e12) return 1e26 * Math.pow(time / 1e-32, 0.5);
  return 1e26 * Math.pow(1e12 / 1e-32, 0.5) * Math.pow(time / 1e12, 0.67);
};

const getCurrentEpoch = (frame: number): CosmicEpoch => {
  return (
    EPOCHS.find((e) => frame >= e.startFrame && frame < e.endFrame) ||
    EPOCHS[EPOCHS.length - 1]
  );
};

// =====================================================
// 组件：普朗克时期 - 量子泡沫
// =====================================================
const PlanckEra = ({
  frame,
  intensity,
}: {
  frame: number;
  intensity: number;
}) => {
  const particles = useMemo(
    () =>
      Array.from({ length: 150 }).map((_, i) => ({
        x: getPiRandom(i * 7, 540, 740),
        y: getPiRandom(i * 11, 260, 460),
        size: getPiRandom(i * 13, 2, 6),
        phase: getPiRandom(i * 17, 0, Math.PI * 2),
        speed: getPiRandom(i * 19, 30, 80),
        hue: getPiRandom(i * 23, 240, 300),
      })),
    [],
  );

  return (
    <g opacity={intensity}>
      <defs>
        <radialGradient id="quantumFoam">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity={0.9} />
          <stop offset="30%" stopColor="#CCAAFF" stopOpacity={0.6} />
          <stop offset="70%" stopColor="#6644AA" stopOpacity={0.3} />
          <stop offset="100%" stopColor="#220044" stopOpacity={0} />
        </radialGradient>
      </defs>
      {particles.map((p, i) => {
        const t = frame * 0.05;
        const wave1 = Math.sin(t * p.speed * 0.01 + p.phase) * 15;
        const wave2 = Math.cos(t * p.speed * 0.015 + p.phase * 1.3) * 10;
        const size = p.size * (1 + Math.sin(t * 0.2 + i) * 0.3);
        return (
          <circle
            key={i}
            cx={p.x + wave1}
            cy={p.y + wave2}
            r={size}
            fill={`hsla(${p.hue}, 80%, 70%, ${0.5 + Math.sin(t + p.phase) * 0.3})`}
          />
        );
      })}
    </g>
  );
};

// =====================================================
// 组件：暴胀时期 - 指数膨胀
// =====================================================
const InflationEra = ({
  frame,
  progress,
}: {
  frame: number;
  progress: number;
}) => {
  const expansion = useMemo(
    () => Math.pow(PHYSICAL_CONSTANTS.INFLATION_FACTOR, progress),
    [progress],
  );

  return (
    <g>
      <defs>
        <radialGradient id="inflationGrad">
          <stop offset="0%" stopColor="#FFEEAA" />
          <stop offset="20%" stopColor="#FFCC66" />
          <stop offset="50%" stopColor="#FF8822" />
          <stop offset="100%" stopColor="#000000" stopOpacity={0} />
        </radialGradient>
      </defs>
      <circle
        cx={640}
        cy={360}
        r={30 * expansion}
        fill="url(#inflationGrad)"
        opacity={1 - progress * 0.3}
      />
      {/* 视界 */}
      <circle
        cx={640}
        cy={360}
        r={60 * expansion}
        fill="none"
        stroke="hsla(40, 100%, 60%, 0.4)"
        strokeWidth={2}
        strokeDasharray="8,4"
        opacity={1 - progress}
      />
      <circle
        cx={640}
        cy={360}
        r={100 * expansion}
        fill="none"
        stroke="hsla(40, 100%, 50%, 0.2)"
        strokeWidth={1}
        strokeDasharray="20,10"
        opacity={0.8 - progress * 0.5}
      />
      {/* 量子涨落 */}
      {Array.from({ length: 50 }).map((_, i) => {
        const angle = (i / 50) * Math.PI * 2 + frame * 0.01;
        const r = 40 * expansion + Math.sin(frame * 0.1 + i) * 10;
        return (
          <circle
            key={i}
            cx={640 + Math.cos(angle) * r}
            cy={360 + Math.sin(angle) * r * 0.7}
            r={2}
            fill={`hsla(${30 + i * 2}, 100%, 60%, ${0.6})`}
          />
        );
      })}
    </g>
  );
};

// =====================================================
// 组件：再加热 - 暴胀结束
// =====================================================
const Reheating = ({
  frame,
  intensity,
}: {
  frame: number;
  intensity: number;
}) => {
  return (
    <g opacity={intensity}>
      {/* 冲击波环 */}
      {Array.from({ length: 5 }).map((_, i) => {
        const delay = i * 10;
        const age = Math.max(0, frame - 40 - delay);
        const radius = age * 8;
        const alpha = Math.max(0, 1 - age / 60);
        return (
          <circle
            key={i}
            cx={640}
            cy={360}
            r={radius}
            fill="none"
            stroke={`hsla(${30 + i * 10}, 100%, 60%, ${alpha * 0.6})`}
            strokeWidth={6 - i}
          />
        );
      })}
      {/* 粒子产生 */}
      {Array.from({ length: 300 }).map((_, i) => {
        const angle = getPiRandom(i * 7, 0, Math.PI * 2);
        const speed = getPiRandom(i * 11, 2, 8);
        const distance = Math.max(0, (frame - 40) * speed);
        const x = 640 + Math.cos(angle) * distance;
        const y = 360 + Math.sin(angle) * distance * 0.7;
        const alpha = Math.max(0, 1 - distance / 400);
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={2}
            fill={`hsla(${getPiRandom(i * 13, 20, 50)}, 100%, 60%, ${alpha})`}
          />
        );
      })}
    </g>
  );
};

// =====================================================
// 组件：夸克-胶子等离子体
// =====================================================
const QuarkGluonPlasma = ({
  frame,
  intensity,
}: {
  frame: number;
  intensity: number;
}) => {
  const quarks = useMemo(
    () =>
      Array.from({ length: 120 }).map((_, i) => ({
        x: getPiRandom(i * 7, 440, 840),
        y: getPiRandom(i * 11, 160, 560),
        color: ["#FF4444", "#44FF44", "#4444FF"][i % 3] as string,
        type: ["红", "绿", "蓝"][i % 3] as string,
        vx: getPiRandom(i * 13, -5, 5),
        vy: getPiRandom(i * 17, -3, 3),
      })),
    [],
  );

  return (
    <g opacity={intensity}>
      <defs>
        <radialGradient id="qgpGrad">
          <stop offset="0%" stopColor="#FFAA44" stopOpacity={0.9} />
          <stop offset="40%" stopColor="#CC4400" stopOpacity={0.5} />
          <stop offset="100%" stopColor="#220000" stopOpacity={0} />
        </radialGradient>
      </defs>
      <circle cx={640} cy={360} r={250} fill="url(#qgpGrad)" />
      {/* 胶子场 */}
      <circle cx={640} cy={360} r={200} fill="hsla(30, 100%, 40%, 0.2)" />
      {/* 夸克 */}
      {quarks.map((q, i) => {
        const x = q.x + q.vx * frame * 0.5;
        const y = q.y + q.vy * frame * 0.5;
        const wrapX = ((x - 440) % 400) + 440;
        const wrapY = ((y - 160) % 400) + 160;
        return (
          <g key={i}>
            <circle cx={wrapX} cy={wrapY} r={5} fill={q.color} />
            <text
              x={wrapX}
              y={wrapY + 1}
              textAnchor="middle"
              fill="white"
              fontSize={6}
              fontWeight="bold"
            >
              {q.type}
            </text>
          </g>
        );
      })}
    </g>
  );
};

// =====================================================
// 组件：核合成 - 元素形成
// =====================================================
const Nucleosynthesis = ({ intensity }: { intensity: number }) => {
  const elements = useMemo(
    () =>
      Array.from({ length: 100 }).map((_, i) => {
        const r = getPiRandom(i * 7, 0, 1);
        let type: string, abundance: number, color: string, radius: number;
        if (r < 0.76) {
          type = "¹H";
          abundance = 76;
          color = "#4488FF";
          radius = 3;
        } else if (r < 0.998) {
          type = "⁴He";
          abundance = 24;
          color = "#FFAA44";
          radius = 6;
        } else {
          type = "⁷Li";
          abundance = 0.01;
          color = "#AA44FF";
          radius = 4;
        }
        return {
          x: getPiRandom(i * 11, 200, 1080),
          y: getPiRandom(i * 13, 100, 620),
          type,
          abundance,
          color,
          radius,
        };
      }),
    [],
  );

  return (
    <g opacity={intensity}>
      {/* 丰度标注 */}
      <g transform="translate(50, 80)">
        <text fill="white" fontSize={12} fontWeight="bold">
          原初核合成丰度
        </text>
        <text y={20} fill="#4488FF" fontSize={10}>
          氢 (¹H): 76%
        </text>
        <text y={35} fill="#FFAA44" fontSize={10}>
          氦 (⁴He): 24%
        </text>
        <text y={50} fill="#AA44FF" fontSize={10}>
          锂 (⁷Li): 0.01%
        </text>
      </g>
      {/* 原子核 */}
      {elements.map((el, i) => (
        <g key={i}>
          <circle
            cx={el.x}
            cy={el.y}
            r={el.radius}
            fill={el.color}
            opacity={0.8}
          />
          <text
            x={el.x}
            y={el.y + 1}
            textAnchor="middle"
            fill="white"
            fontSize={el.radius * 1.2}
            fontWeight="bold"
          >
            {el.type}
          </text>
        </g>
      ))}
    </g>
  );
};

// =====================================================
// 组件：CMB - 复合时期（带各向异性）
// =====================================================
const CMBObservation = ({
  frame,
  temperature,
}: {
  frame: number;
  temperature: number;
}) => {
  const opacity = smoothstep(2000, 3000, temperature);

  return (
    <g opacity={opacity}>
      <defs>
        <radialGradient id="cmbGrad">
          <stop offset="0%" stopColor="#FF6600" stopOpacity={0.7} />
          <stop offset="50%" stopColor="#CC4400" stopOpacity={0.4} />
          <stop offset="100%" stopColor="#220000" stopOpacity={0} />
        </radialGradient>
      </defs>
      {/* CMB壳层 */}
      <circle cx={640} cy={360} r={350} fill="url(#cmbGrad)" />
      {/* 各向异性图案 */}
      {Array.from({ length: 64 }).map((_, i) => {
        const theta = (i / 64) * Math.PI * 2;
        const phi = getPiRandom(i * 7, 0, Math.PI);
        const r = 300 + getPiRandom(i * 11, -30, 30) * Math.sin(frame * 0.02);
        const temp = 2.725 + getPiRandom(i * 13, -0.001, 0.001);
        const hue = temp > 2.725 ? 20 : 40;
        return (
          <circle
            key={i}
            cx={640 + Math.cos(theta) * r}
            cy={360 + Math.sin(theta) * r * Math.sin(phi)}
            r={8}
            fill={`hsla(${hue}, 100%, 50%, 0.3)`}
          />
        );
      })}
      {/* 光子轨迹 */}
      {Array.from({ length: 100 }).map((_, i) => {
        const angle = (i / 100) * Math.PI * 2;
        const r = 320;
        return (
          <line
            key={i}
            x1={640 + Math.cos(angle) * r}
            y1={360 + Math.sin(angle) * r}
            x2={640 + Math.cos(angle) * (r + 50)}
            y2={360 + Math.sin(angle) * (r + 50)}
            stroke={`hsla(${30 + (temperature / 3000) * 30}, 100%, 50%, 0.2)`}
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
};

// =====================================================
// 组件：结构形成
// =====================================================
const StructureFormation = ({
  frame,
  time,
}: {
  frame: number;
  time: number;
}) => {
  const scale = Math.min(1, Math.max(0, Math.log10(time / 1e13) / 6));

  // LOD: 根据尺度调整粒子数
  const particleCount = scale < 0.3 ? 20 : scale < 0.7 ? 40 : 80;

  const darkMatter = useMemo(
    () =>
      Array.from({ length: particleCount }).map((_, i) => ({
        x: getPiRandom(i * 7, 80, 1200),
        y: getPiRandom(i * 11, 60, 660),
        mass: getPiRandom(i * 13, 10, 50),
        vx: getPiRandom(i * 17, -0.2, 0.2),
        vy: getPiRandom(i * 19, -0.15, 0.15),
      })),
    [particleCount],
  );

  return (
    <g opacity={scale}>
      {/* 暗物质晕 */}
      {darkMatter.map((dm, i) => {
        const x = dm.x + dm.vx * frame;
        const y = dm.y + dm.vy * frame;
        return (
          <g key={i}>
            <circle
              cx={x}
              cy={y}
              r={dm.mass * scale}
              fill="hsla(260, 40%, 30%, 0.15)"
            />
            <circle
              cx={x}
              cy={y}
              r={dm.mass * 0.3 * scale}
              fill="hsla(280, 50%, 40%, 0.25)"
            />
          </g>
        );
      })}
      {/* 第一代恒星 (Pop III) */}
      {time > 1.5e8 * 3.15e7 && (
        <g>
          {Array.from({ length: 30 }).map((_, i) => {
            const x = getPiRandom(i * 23, 150, 1130);
            const y = getPiRandom(i * 29, 80, 640);
            const brightness = Math.min(
              1,
              (time - 1.5e8 * 3.15e7) / (1e9 * 3.15e7),
            );
            const twinkle = 0.8 + Math.sin(frame * 0.1 + i) * 0.2;
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={4 * brightness * twinkle}
                fill={`hsla(${getPiRandom(i * 31, 30, 50)}, 100%, 80%, ${brightness})`}
                filter="url(#starGlow)"
              />
            );
          })}
        </g>
      )}
    </g>
  );
};

// =====================================================
// 组件：时间轴控制
// =====================================================
const Timeline = ({
  currentFrame,
  totalFrames,
  onEpochClick,
}: {
  currentFrame: number;
  totalFrames: number;
  onEpochClick: (frame: number) => void;
}) => {
  return (
    <g transform="translate(20, 680)">
      <rect width={1240} height={30} fill="rgba(0,0,0,0.5)" rx={5} />
      {/* 时期标记 */}
      {EPOCHS.map((epoch, i) => {
        const x = (epoch.startFrame / totalFrames) * 1240;
        const width =
          ((epoch.endFrame - epoch.startFrame) / totalFrames) * 1240;
        const isActive =
          currentFrame >= epoch.startFrame && currentFrame < epoch.endFrame;
        return (
          <g
            key={i}
            style={{ cursor: "pointer" }}
            onClick={() => onEpochClick(epoch.startFrame)}
          >
            <rect
              x={x}
              y={0}
              width={width}
              height={30}
              fill={
                isActive ? "rgba(100,150,255,0.4)" : "rgba(100,100,100,0.2)"
              }
            />
            <text
              x={x + width / 2}
              y={20}
              textAnchor="middle"
              fill="white"
              fontSize={8}
              opacity={width > 50 ? 1 : 0}
            >
              {epoch.name}
            </text>
          </g>
        );
      })}
      {/* 进度指示器 */}
      <circle
        cx={(currentFrame / totalFrames) * 1240}
        cy={15}
        r={5}
        fill="#4488FF"
      />
    </g>
  );
};

// =====================================================
// 组件：物理信息面板
// =====================================================
const PhysicsPanel = ({
  time,
  temp,
  scaleFactor,
}: {
  time: number;
  temp: number;
  scaleFactor: number;
}) => {
  const redshift = temp / PHYSICAL_CONSTANTS.CMB_TEMPERATURE - 1;
  const density = 1 / Math.pow(scaleFactor, 3);
  const horizon = (3e8 * time) / (scaleFactor || 1);

  return (
    <g transform="translate(20, 100)">
      <rect
        width={220}
        height={160}
        fill="rgba(0,0,0,0.6)"
        rx={8}
        stroke="rgba(255,255,255,0.2)"
        strokeWidth={1}
      />
      <text x={10} y={20} fill="white" fontSize={11} fontWeight="bold">
        宇宙学参数
      </text>
      <text x={10} y={40} fill="#AAAAAA" fontSize={9}>
        温度 (T): {temp.toExponential(2)} K
      </text>
      <text x={10} y={55} fill="#AAAAAA" fontSize={9}>
        红移 (z):{" "}
        {redshift > 1e6 ? redshift.toExponential(2) : redshift.toFixed(1)}
      </text>
      <text x={10} y={70} fill="#AAAAAA" fontSize={9}>
        尺度因子 (a): {scaleFactor.toExponential(2)}
      </text>
      <text x={10} y={85} fill="#AAAAAA" fontSize={9}>
        密度 (ρ): {density.toExponential(2)} ρ₀
      </text>
      <text x={10} y={100} fill="#AAAAAA" fontSize={9}>
        视界: {horizon.toExponential(2)} m
      </text>
      <text x={10} y="125" fill="#66AAFF" fontSize={8}>
        Ωₘ ={" "}
        {PHYSICAL_CONSTANTS.BARYON_DENSITY +
          PHYSICAL_CONSTANTS.DARK_MATTER_DENSITY}
      </text>
      <text x="10" y="140" fill="#FF66AA" fontSize="8">
        ΩΛ = {PHYSICAL_CONSTANTS.DARK_ENERGY_DENSITY}
      </text>
    </g>
  );
};

// =====================================================
// 主组件
// =====================================================
export const BigBangUniverse = () => {
  const frame = useCurrentFrame();
  const { width, durationInFrames } = useVideoConfig();

  const physicalTime = getPhysicalTime(frame);
  const temperature = getTemperature(physicalTime);
  const scaleFactor = getScaleFactor(physicalTime);
  const currentEpoch = getCurrentEpoch(frame);

  // 计算各时期强度（带缓动）
  const planckIntensity = Math.max(0, 1 - frame / 15);
  const inflationProgress = smoothstep(20, 40, frame);
  const reheatingIntensity =
    smoothstep(40, 50, frame) * (1 - smoothstep(50, 60, frame));
  const quarkIntensity =
    smoothstep(70, 80, frame) * (1 - smoothstep(90, 100, frame));
  const nucleosynthesisIntensity =
    smoothstep(130, 140, frame) * (1 - smoothstep(150, 160, frame));
  const cmbOpacity = smoothstep(2800, 3000, temperature);
  const structureOpacity = smoothstep(1e13, 1e15, physicalTime);

  const handleEpochClick = useCallback((targetFrame: number) => {
    // 在实际应用中，这里会跳转到特定帧
    console.log("Jump to frame:", targetFrame);
  }, []);

  return (
    <svg
      width="100%"
      height="100%"
      style={{ background: tempToColor(temperature) }}
    >
      <defs>
        <filter id="starGlow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <radialGradient id="bgGradient">
          <stop offset="0%" stopColor="#0a0a1a" />
          <stop offset="100%" stopColor="#000000" />
        </radialGradient>
      </defs>

      {/* 背景 */}
      {temperature < 1000 && (
        <rect width="100%" height="100%" fill="url(#bgGradient)" />
      )}

      {/* 普朗克时期 */}
      {planckIntensity > 0 && (
        <PlanckEra frame={frame} intensity={planckIntensity} />
      )}

      {/* 暴胀时期 */}
      {inflationProgress > 0 && (
        <InflationEra frame={frame} progress={inflationProgress} />
      )}

      {/* 再加热 */}
      {reheatingIntensity > 0 && (
        <Reheating frame={frame} intensity={reheatingIntensity} />
      )}

      {/* 夸克-胶子等离子体 */}
      {quarkIntensity > 0 && (
        <QuarkGluonPlasma frame={frame} intensity={quarkIntensity} />
      )}

      {/* 核合成 */}
      {nucleosynthesisIntensity > 0 && (
        <Nucleosynthesis intensity={nucleosynthesisIntensity} />
      )}

      {/* CMB */}
      {cmbOpacity > 0 && (
        <CMBObservation frame={frame} temperature={temperature} />
      )}

      {/* 结构形成 */}
      {structureOpacity > 0 && (
        <StructureFormation frame={frame} time={physicalTime} />
      )}

      {/* UI层 */}
      {/* 标题和时期信息 */}
      <g transform="translate(20, 30)">
        <text fill="white" fontSize={18} fontWeight="bold">
          宇宙大爆炸 - 真实物理演化
        </text>
        <text y={25} fill="#66AAFF" fontSize={13}>
          {currentEpoch.name} | {currentEpoch.nameEn}
        </text>
        <text y={45} fill="#AAAAAA" fontSize={11}>
          {currentEpoch.description}
        </text>
        <text y={65} fill="white" fontSize={12}>
          t = {formatTime(physicalTime)}
        </text>
      </g>

      {/* 物理参数面板 */}
      <PhysicsPanel
        time={physicalTime}
        temp={temperature}
        scaleFactor={scaleFactor}
      />

      {/* 时间轴 */}
      <Timeline
        currentFrame={frame}
        totalFrames={durationInFrames}
        onEpochClick={handleEpochClick}
      />

      {/* 帧率显示 */}
      <text
        x={width - 20}
        y={30}
        textAnchor="end"
        fill="white"
        fontSize={10}
        opacity={0.5}
      >
        Frame: {frame} / {durationInFrames}
      </text>
    </svg>
  );
};
