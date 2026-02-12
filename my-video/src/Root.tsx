import "./index.css";
import { Composition } from "remotion";
import { MyComposition, RollingBall } from "./Composition";
import { FractalTree } from "./FractalTree";
import { RerankingFlow } from "./RerankingFlow";
import { Fireflies } from "./Fireflies";
import { ThreeSceneFallingCat } from "./ThreeSceneFallingCat";
import { BigBangUniverse } from "./BigBangUniverse";
import {
  ProjectApprovalFlow,
  ProjectApprovalFlowSchema,
} from "./ProjectApprovalFlow";
import {
  ProjectApprovalFlowDetailed,
  ProjectApprovalFlowDetailedSchema,
} from "./ProjectApprovalFlowDetailed";
import {
  ProjectApprovalFlowEnhanced,
  ProjectApprovalFlowEnhancedSchema,
} from "./ProjectApprovalFlowEnhanced";

import { ProjectApprovalFlowChineseV2 } from "./ProjectApprovalFlowChineseV2";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AnimationSelector"
        component={MyComposition}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="RollingBall"
        component={RollingBall}
        durationInFrames={120}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="FractalTree"
        component={FractalTree}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="RerankingFlow"
        component={RerankingFlow}
        durationInFrames={600}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="Fireflies"
        component={Fireflies}
        durationInFrames={54000}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ThreeSceneFallingCat"
        component={ThreeSceneFallingCat}
        durationInFrames={180}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="BigBangUniverse"
        component={BigBangUniverse}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ProjectApprovalFlow"
        component={ProjectApprovalFlow}
        schema={ProjectApprovalFlowSchema}
        defaultProps={{ titleText: "立项审批流程" }}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ProjectApprovalFlowDetailed"
        component={ProjectApprovalFlowDetailed}
        schema={ProjectApprovalFlowDetailedSchema}
        defaultProps={{ titleText: "详细审批流程" }}
        durationInFrames={450}
        fps={30}
        width={1280}
        height={720}
      />
      <Composition
        id="ProjectApprovalFlowEnhanced"
        component={ProjectApprovalFlowEnhanced}
        schema={ProjectApprovalFlowEnhancedSchema}
        durationInFrames={450}
        fps={30}
        width={1280}
        height={720}
      />

      <Composition
        id="ProjectApprovalFlowChineseV2"
        component={ProjectApprovalFlowChineseV2}
        durationInFrames={360}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
