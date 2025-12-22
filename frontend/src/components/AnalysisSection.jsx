export default function AnalysisSection() {
  return (
    <div className="card text-center animate-fade-in">
      <div className="py-12">
        <div className="loading-spinner mb-8"></div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          AI가 열심히 분석 중입니다... 🤖
        </h2>
        <div className="flex flex-col gap-3 text-gray-600 max-w-md mx-auto">
          <p className="animate-pulse">🎨 이미지 특징 추출 중...</p>
          <p className="animate-pulse delay-100">🧠 AI 모델 분석 중...</p>
          <p className="animate-pulse delay-200">📊 결과 계산 중...</p>
        </div>
        <div className="mt-8">
          <div className="w-64 mx-auto bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-teto to-aegen h-2 rounded-full animate-pulse w-3/4"></div>
          </div>
          <p className="text-sm text-gray-500 mt-2">잠시만 기다려주세요...</p>
        </div>
      </div>
    </div>
  )
}
