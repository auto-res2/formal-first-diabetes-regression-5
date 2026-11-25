import Spec
/-! 証明に必要なもの（宣言が成り立つことの証明、claims を導く定理）。claims の形式化（claims.json）とは別に置く。 -/

namespace Spec

theorem C03_holds : C03 := rfl

theorem C04_holds : C04 := ⟨rfl, rfl, rfl⟩

theorem C05_holds : C05 := ⟨rfl, rfl, rfl⟩

theorem C06_holds : C06 := ⟨rfl, rfl⟩

theorem C07_holds : C07 := ⟨rfl, rfl⟩

theorem C08_holds : C08 := ⟨rfl, rfl⟩

theorem C09_holds : C09 := rfl

theorem C10_holds : C10 := rfl

theorem C02_holds : C02 :=
  ⟨C03_holds, C04_holds, C05_holds, C06_holds, C07_holds, C08_holds, C09_holds, C10_holds, _, rfl⟩

/-- C02 と、出力された MSE が 3400 を下回ることから、C01 を導く。 -/
theorem C01_of_C02 (outputTestMse : ℚ) :
    C02 → outputTestMse < 3400 → C01 outputTestMse :=
  fun _ below => below

/-- C02 と、出力された MSE が 3400 を下回らないことから、C01 の否定を導く。 -/
theorem not_C01_of_C02 (outputTestMse : ℚ) :
    C02 → ¬ outputTestMse < 3400 → ¬ C01 outputTestMse :=
  fun _ notBelow => notBelow

/-- R01、R02、R03 から Reliable.C03 を導く。 -/
theorem Reliable_C03_of_conditions (preparedDatasets : List Dataset) :
    R01 C03.value preparedDatasets →
    R02 C03.value preparedDatasets →
    R03 C03.value preparedDatasets →
    Reliable.C03 preparedDatasets :=
  fun h0 h1 h2 => ⟨h0, h1, h2⟩

/-- R04、R05、R06、R07、R08、R09 から Reliable.C04 を導く。 -/
theorem Reliable_C04_of_conditions (observedLoadCalls : List Call)
    (preparedDatasets : List Dataset) (loadedFileChecksums : List String)
    (loadedShapes : List (List ℕ)) (preparedFileColumnChecksums : List (List String))
    (loadedColumnChecksums : List (List String)) (observedFeatureColumns : List String)
    (observedTargetColumn : String) :
    R04 C04.value →
    R05 C04.value observedLoadCalls →
    R06 preparedDatasets loadedFileChecksums →
    R07 preparedDatasets loadedShapes →
    R08 preparedFileColumnChecksums loadedColumnChecksums →
    R09 C04.value observedFeatureColumns observedTargetColumn →
    Reliable.C04 observedLoadCalls preparedDatasets loadedFileChecksums loadedShapes
      preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn :=
  fun h0 h1 h2 h3 h4 h5 => ⟨h0, h1, h2, h3, h4, h5⟩

/-- R10、R11、R12、R13、R14、R15、R16、R17 から Reliable.C05 を導く。 -/
theorem Reliable_C05_of_conditions (observedSplitCalls : List Call)
    (loadedColumnChecksums : List (List String)) (splitInputColumnChecksums : List (List String))
    (observedTrainIndex : List ℕ) (observedTestIndex : List ℕ) (splitInputSampleCount : ℕ)
    (observedSplitSeeds : List String) :
    R10 C05.value →
    R11 C05.value observedSplitCalls →
    R12 loadedColumnChecksums splitInputColumnChecksums →
    R13 observedTrainIndex observedTestIndex →
    R14 splitInputSampleCount observedTrainIndex observedTestIndex →
    R15 →
    R16 C05.value observedSplitSeeds →
    R17 C05.value →
    Reliable.C05 observedSplitCalls loadedColumnChecksums splitInputColumnChecksums observedTrainIndex
      observedTestIndex splitInputSampleCount observedSplitSeeds :=
  fun h0 h1 h2 h3 h4 h5 h6 h7 => ⟨h0, h1, h2, h3, h4, h5, h6, h7⟩

/-- R18、R19、R20、R21 から Reliable.C06 を導く。 -/
theorem Reliable_C06_of_conditions (observedFitCalls : List Call)
    (splitTrainChecksums : List String) (fitInputChecksums : List String) (fitInputIndex : List ℕ)
    (observedTestIndex : List ℕ) :
    R18 C06.value →
    R19 C06.value observedFitCalls →
    R20 splitTrainChecksums fitInputChecksums →
    R21 fitInputIndex observedTestIndex →
    Reliable.C06 observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedTestIndex :=
  fun h0 h1 h2 h3 => ⟨h0, h1, h2, h3⟩

/-- R22、R23、R24、R25、R26 から Reliable.C07 を導く。 -/
theorem Reliable_C07_of_conditions (observedPredictCalls : List Call)
    (fittedModelChecksums : List String) (predictModelChecksums : List String)
    (splitTestFeatureChecksums : List String) (predictInputChecksums : List String)
    (splitTestTargetChecksums : List String) (predictInputColumnChecksums : List (List String)) :
    R22 C07.value →
    R23 C07.value observedPredictCalls →
    R24 fittedModelChecksums predictModelChecksums →
    R25 splitTestFeatureChecksums predictInputChecksums →
    R26 splitTestTargetChecksums predictInputColumnChecksums →
    Reliable.C07 observedPredictCalls fittedModelChecksums predictModelChecksums
      splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums
      predictInputColumnChecksums :=
  fun h0 h1 h2 h3 h4 => ⟨h0, h1, h2, h3, h4⟩

/-- R27、R28、R29、R30、R31、R32 から Reliable.C08 を導く。 -/
theorem Reliable_C08_of_conditions (observedMetricCalls : List Call)
    (predictOutputChecksums : List String) (metricPredictionChecksums : List String)
    (splitTestTargetChecksums : List String) (metricTargetChecksums : List String)
    (metricTargetSampleCounts : List ℕ) (metricPredictionSampleCounts : List ℕ)
    (metricReturnedValues : List ℚ) (outputTestMse : ℚ) :
    R27 C08.value →
    R28 C08.value observedMetricCalls →
    R29 predictOutputChecksums metricPredictionChecksums →
    R30 splitTestTargetChecksums metricTargetChecksums →
    R31 metricTargetSampleCounts metricPredictionSampleCounts →
    R32 metricReturnedValues outputTestMse →
    Reliable.C08 observedMetricCalls predictOutputChecksums metricPredictionChecksums
      splitTestTargetChecksums metricTargetChecksums metricTargetSampleCounts
      metricPredictionSampleCounts metricReturnedValues outputTestMse :=
  fun h0 h1 h2 h3 h4 h5 => ⟨h0, h1, h2, h3, h4, h5⟩

/-- R33、R34 から Reliable.C09 を導く。 -/
theorem Reliable_C09_of_conditions (observedEnvironment : Environment)
    (configuredParallelism : Parallelism) (finalMaxMemoryMebibytes : ℕ)
    (sampledUsage : SampledUsage) :
    R33 C09.value observedEnvironment configuredParallelism finalMaxMemoryMebibytes →
    R34 sampledUsage configuredParallelism finalMaxMemoryMebibytes →
    Reliable.C09 observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage :=
  fun h0 h1 => ⟨h0, h1⟩

/-- R35、R36、R37 から Reliable.C10 を導く。 -/
theorem Reliable_C10_of_conditions (observedCommit : String) (observedLanguage : String)
    (observedDependencies : List (String × String)) (observedSetupCommand : List String)
    (observedCommand : List String) (observedEnvironmentVariables : List (String × String)) :
    R35 C10.value observedCommit →
    R36 C10.value observedLanguage observedDependencies →
    R37 C10.value observedSetupCommand observedCommand observedEnvironmentVariables →
    Reliable.C10 observedCommit observedLanguage observedDependencies observedSetupCommand
      observedCommand observedEnvironmentVariables :=
  fun h0 h1 h2 => ⟨h0, h1, h2⟩

/-- Reliable.C03、Reliable.C04、Reliable.C05、Reliable.C06、Reliable.C07、Reliable.C08、Reliable.C09、Reliable.C10 から Reliable.C02 を導く。 -/
theorem Reliable_C02_of_conditions (preparedDatasets : List Dataset)
    (observedLoadCalls : List Call) (loadedFileChecksums : List String)
    (loadedShapes : List (List ℕ)) (preparedFileColumnChecksums : List (List String))
    (loadedColumnChecksums : List (List String)) (observedFeatureColumns : List String)
    (observedTargetColumn : String) (observedSplitCalls : List Call)
    (splitInputColumnChecksums : List (List String)) (observedTrainIndex : List ℕ)
    (observedTestIndex : List ℕ) (splitInputSampleCount : ℕ) (observedSplitSeeds : List String)
    (observedFitCalls : List Call) (splitTrainChecksums : List String)
    (fitInputChecksums : List String) (fitInputIndex : List ℕ) (observedPredictCalls : List Call)
    (fittedModelChecksums : List String) (predictModelChecksums : List String)
    (splitTestFeatureChecksums : List String) (predictInputChecksums : List String)
    (splitTestTargetChecksums : List String) (predictInputColumnChecksums : List (List String))
    (observedMetricCalls : List Call) (predictOutputChecksums : List String)
    (metricPredictionChecksums : List String) (metricTargetChecksums : List String)
    (metricTargetSampleCounts : List ℕ) (metricPredictionSampleCounts : List ℕ)
    (metricReturnedValues : List ℚ) (outputTestMse : ℚ) (observedEnvironment : Environment)
    (configuredParallelism : Parallelism) (finalMaxMemoryMebibytes : ℕ)
    (sampledUsage : SampledUsage) (observedCommit : String) (observedLanguage : String)
    (observedDependencies : List (String × String)) (observedSetupCommand : List String)
    (observedCommand : List String) (observedEnvironmentVariables : List (String × String)) :
    Reliable.C03 preparedDatasets →
    Reliable.C04 observedLoadCalls preparedDatasets loadedFileChecksums loadedShapes
      preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn →
    Reliable.C05 observedSplitCalls loadedColumnChecksums splitInputColumnChecksums observedTrainIndex
      observedTestIndex splitInputSampleCount observedSplitSeeds →
    Reliable.C06 observedFitCalls splitTrainChecksums fitInputChecksums fitInputIndex observedTestIndex →
    Reliable.C07 observedPredictCalls fittedModelChecksums predictModelChecksums
      splitTestFeatureChecksums predictInputChecksums splitTestTargetChecksums
      predictInputColumnChecksums →
    Reliable.C08 observedMetricCalls predictOutputChecksums metricPredictionChecksums
      splitTestTargetChecksums metricTargetChecksums metricTargetSampleCounts
      metricPredictionSampleCounts metricReturnedValues outputTestMse →
    Reliable.C09 observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage →
    Reliable.C10 observedCommit observedLanguage observedDependencies observedSetupCommand
      observedCommand observedEnvironmentVariables →
    Reliable.C02 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes
      preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn
      observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex
      splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums
      fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums
      predictModelChecksums splitTestFeatureChecksums predictInputChecksums
      splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls
      predictOutputChecksums metricPredictionChecksums metricTargetChecksums
      metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse
      observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit
      observedLanguage observedDependencies observedSetupCommand observedCommand
      observedEnvironmentVariables :=
  fun h0 h1 h2 h3 h4 h5 h6 h7 => ⟨h0, h1, h2, h3, h4, h5, h6, h7⟩

/-- Reliable.C02 から Reliable.C01 を導く。 -/
theorem Reliable_C01_of_conditions (preparedDatasets : List Dataset)
    (observedLoadCalls : List Call) (loadedFileChecksums : List String)
    (loadedShapes : List (List ℕ)) (preparedFileColumnChecksums : List (List String))
    (loadedColumnChecksums : List (List String)) (observedFeatureColumns : List String)
    (observedTargetColumn : String) (observedSplitCalls : List Call)
    (splitInputColumnChecksums : List (List String)) (observedTrainIndex : List ℕ)
    (observedTestIndex : List ℕ) (splitInputSampleCount : ℕ) (observedSplitSeeds : List String)
    (observedFitCalls : List Call) (splitTrainChecksums : List String)
    (fitInputChecksums : List String) (fitInputIndex : List ℕ) (observedPredictCalls : List Call)
    (fittedModelChecksums : List String) (predictModelChecksums : List String)
    (splitTestFeatureChecksums : List String) (predictInputChecksums : List String)
    (splitTestTargetChecksums : List String) (predictInputColumnChecksums : List (List String))
    (observedMetricCalls : List Call) (predictOutputChecksums : List String)
    (metricPredictionChecksums : List String) (metricTargetChecksums : List String)
    (metricTargetSampleCounts : List ℕ) (metricPredictionSampleCounts : List ℕ)
    (metricReturnedValues : List ℚ) (outputTestMse : ℚ) (observedEnvironment : Environment)
    (configuredParallelism : Parallelism) (finalMaxMemoryMebibytes : ℕ)
    (sampledUsage : SampledUsage) (observedCommit : String) (observedLanguage : String)
    (observedDependencies : List (String × String)) (observedSetupCommand : List String)
    (observedCommand : List String) (observedEnvironmentVariables : List (String × String)) :
    Reliable.C02 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes
      preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn
      observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex
      splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums
      fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums
      predictModelChecksums splitTestFeatureChecksums predictInputChecksums
      splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls
      predictOutputChecksums metricPredictionChecksums metricTargetChecksums
      metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse
      observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit
      observedLanguage observedDependencies observedSetupCommand observedCommand
      observedEnvironmentVariables →
    Reliable.C01 preparedDatasets observedLoadCalls loadedFileChecksums loadedShapes
      preparedFileColumnChecksums loadedColumnChecksums observedFeatureColumns observedTargetColumn
      observedSplitCalls splitInputColumnChecksums observedTrainIndex observedTestIndex
      splitInputSampleCount observedSplitSeeds observedFitCalls splitTrainChecksums
      fitInputChecksums fitInputIndex observedPredictCalls fittedModelChecksums
      predictModelChecksums splitTestFeatureChecksums predictInputChecksums
      splitTestTargetChecksums predictInputColumnChecksums observedMetricCalls
      predictOutputChecksums metricPredictionChecksums metricTargetChecksums
      metricTargetSampleCounts metricPredictionSampleCounts metricReturnedValues outputTestMse
      observedEnvironment configuredParallelism finalMaxMemoryMebibytes sampledUsage observedCommit
      observedLanguage observedDependencies observedSetupCommand observedCommand
      observedEnvironmentVariables :=
  fun h => h

end Spec
