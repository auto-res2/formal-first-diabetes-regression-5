import Spec
import Proofs
import Values
open Spec Values
open Lean Elab Term in
elab "proved% " theoremName:ident : term => do
  let name ← realizeGlobalConstNoOverloadWithInfo theoremName
  if (← collectAxioms name).contains ``sorryAx then throwError "{name} は証明されていない"
  return mkConst name
/-! 各命題の判定。parse_claims.py が生成する。手で編集しない。 -/
axiom R04_axiom : R04 C04.value
axiom R10_axiom : R10 C05.value
axiom R15_axiom : R15
axiom R17_axiom : R17 C05.value
axiom R18_axiom : R18 C06.value
axiom R22_axiom : R22 C07.value
axiom R27_axiom : R27 C08.value
theorem R01_holds : R01 C03.value preparedDatasets := by decide +kernel
theorem R02_holds : R02 C03.value preparedDatasets := by decide +kernel
theorem R03_holds : R03 C03.value preparedDatasets := by decide +kernel
theorem R05_holds : R05 C04.value observedLoadCalls := by decide +kernel
theorem R06_holds : R06 preparedDatasets loadedFileChecksums := by decide +kernel
theorem R07_holds : R07 preparedDatasets loadedShapes := by decide +kernel
theorem R08_holds : R08 preparedFileColumnChecksums loadedColumnChecksums := by decide +kernel
theorem R09_holds : R09 C04.value observedFeatureColumns observedTargetColumn := by decide +kernel
theorem R11_holds : R11 C05.value observedSplitCalls := by decide +kernel
theorem R12_holds : R12 loadedColumnChecksums splitInputColumnChecksums := by decide +kernel
theorem R13_holds : R13 observedTrainIndex observedTestIndex := by decide +kernel
theorem R14_holds : R14 splitInputSampleCount observedTrainIndex observedTestIndex := by decide +kernel
theorem R16_holds : R16 C05.value observedSplitSeeds := by decide +kernel
theorem R19_holds : R19 C06.value observedFitCalls := by decide +kernel
theorem R20_holds : R20 splitTrainChecksums fitInputChecksums := by decide +kernel
theorem R21_holds : R21 fitInputIndex observedTestIndex := by decide +kernel
theorem R23_holds : R23 C07.value observedPredictCalls := by decide +kernel
theorem R24_holds : R24 fittedModelChecksums predictModelChecksums := by decide +kernel
theorem R25_holds : R25 splitTestFeatureChecksums predictInputChecksums := by decide +kernel
theorem R26_holds : R26 splitTestTargetChecksums predictInputColumnChecksums := by decide +kernel
theorem R28_holds : R28 C08.value observedMetricCalls := by decide +kernel
theorem R29_holds : R29 predictOutputChecksums metricPredictionChecksums := by decide +kernel
theorem R30_holds : R30 splitTestTargetChecksums metricTargetChecksums := by decide +kernel
theorem R31_holds : R31 metricTargetSampleCounts metricPredictionSampleCounts := by decide +kernel
theorem R32_holds : R32 metricReturnedValues outputTestMse := by decide +kernel
theorem R33_fails : ¬ (R33 C09.value observedEnvironment configuredParallelism finalMaxMemoryMebibytes) := by decide +kernel
theorem R34_holds : R34 sampledUsage configuredParallelism finalMaxMemoryMebibytes := by decide +kernel
theorem R35_holds : R35 C10.value observedCommit := by decide +kernel
theorem R36_holds : R36 C10.value observedLanguage observedDependencies := by decide +kernel
theorem R37_holds : R37 C10.value observedSetupCommand observedCommand observedEnvironmentVariables := by decide +kernel
theorem C01_fails : ¬ (C01 outputTestMse) := not_C01_of_C02 _ C02_holds (by decide +kernel)
theorem Reliable.C03_holds : Reliable.C03 preparedDatasets := Reliable_C03_of_conditions _ R01_holds R02_holds R03_holds
theorem Reliable.C04_holds : Reliable.C04 observedLoadCalls preparedDatasets loadedFileChecksums loadedShapes preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn := Reliable_C04_of_conditions _ _ _ _ _ _ _ _ R04_axiom R05_holds R06_holds R07_holds R08_holds R09_holds
theorem Reliable.C05_holds : Reliable.C05 observedSplitCalls loadedColumnChecksums splitInputColumnChecksums observedTrainIndex observedTestIndex splitInputSampleCount observedSplitSeeds := Reliable_C05_of_conditions _ _ _ _ _ _ _ R10_axiom R11_holds R12_holds R13_holds R14_holds R15_axiom R16_holds R17_axiom
theorem Reliable.C06_holds : Reliable.C06 observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedTestIndex := Reliable_C06_of_conditions _ _ _ _ _ R18_axiom R19_holds R20_holds R21_holds
theorem Reliable.C07_holds : Reliable.C07 observedPredictCalls fittedModelChecksums predictModelChecksums splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums predictInputColumnChecksums := Reliable_C07_of_conditions _ _ _ _ _ _ _ R22_axiom R23_holds R24_holds R25_holds R26_holds
theorem Reliable.C08_holds : Reliable.C08 observedMetricCalls predictOutputChecksums metricPredictionChecksums splitTestTargetChecksums metricTargetChecksums metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse := Reliable_C08_of_conditions _ _ _ _ _ _ _ _ _ R27_axiom R28_holds R29_holds R30_holds R31_holds R32_holds
theorem Reliable.C09_fails : ¬ (Reliable.C09 observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage) := fun h => by first | exact (proved% R33_fails) h.1 | exact (proved% R34_fails) h.2
theorem Reliable.C10_holds : Reliable.C10 observedCommit observedLanguage observedDependencies observedSetupCommand observedCommand observedEnvironmentVariables := Reliable_C10_of_conditions _ _ _ _ _ _ R35_holds R36_holds R37_holds
theorem Reliable.C02_fails : ¬ (Reliable.C02 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums predictModelChecksums splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls predictOutputChecksums metricPredictionChecksums metricTargetChecksums metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit observedLanguage observedDependencies observedSetupCommand observedCommand observedEnvironmentVariables) := fun h => by first | exact (proved% Reliable.C03_fails) h.1 | exact (proved% Reliable.C04_fails) h.2.1 | exact (proved% Reliable.C05_fails) h.2.2.1 | exact (proved% Reliable.C06_fails) h.2.2.2.1 | exact (proved% Reliable.C07_fails) h.2.2.2.2.1 | exact (proved% Reliable.C08_fails) h.2.2.2.2.2.1 | exact (proved% Reliable.C09_fails) h.2.2.2.2.2.2.1 | exact (proved% Reliable.C10_fails) h.2.2.2.2.2.2.2
theorem Reliable.C01_fails : ¬ (Reliable.C01 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums predictModelChecksums splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls predictOutputChecksums metricPredictionChecksums metricTargetChecksums metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit observedLanguage observedDependencies observedSetupCommand observedCommand observedEnvironmentVariables) := fun h => by first | exact (proved% Reliable.C02_fails) h
theorem main_claim : ¬ (C01 outputTestMse) := C01_fails
theorem main_reliability : ¬ (Reliable.C01 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums predictModelChecksums splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls predictOutputChecksums metricPredictionChecksums metricTargetChecksums metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit observedLanguage observedDependencies observedSetupCommand observedCommand observedEnvironmentVariables) := Reliable.C01_fails
