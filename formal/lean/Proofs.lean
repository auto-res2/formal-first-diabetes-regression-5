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

end Spec
