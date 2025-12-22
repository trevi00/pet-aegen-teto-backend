import { useState } from 'react'
import './App.css'
import UploadSection from './components/UploadSection'
import AnalysisSection from './components/AnalysisSection'
import ResultSection from './components/ResultSection'

function App() {
  const [currentStep, setCurrentStep] = useState('upload') // upload, analyzing, result
  const [selectedImage, setSelectedImage] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)

  const handleImageSelect = (image) => {
    setSelectedImage(image)
    setError(null)
  }

  const handleAnalysisStart = async () => {
    if (!selectedImage) return

    setCurrentStep('analyzing')
    setError(null)

    try {
      const formData = new FormData()
      formData.append('image', selectedImage)

      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setAnalysisResult(data)
        setCurrentStep('result')
      } else {
        throw new Error(data.error || '분석 중 오류가 발생했습니다.')
      }
    } catch (err) {
      setError(err.message)
      setCurrentStep('upload')
    }
  }

  const handleReset = () => {
    setCurrentStep('upload')
    setSelectedImage(null)
    setAnalysisResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* 헤더 */}
        <header className="text-center mb-8 animate-fade-in">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-teto to-aegen bg-clip-text text-transparent mb-3">
            🐾 반려동물 에겐 vs 테토 테스트
          </h1>
          <p className="text-gray-600 text-lg">
            AI가 당신의 반려동물이 에겐인지 테토인지 분석해드립니다!
          </p>
        </header>

        {/* 에러 메시지 */}
        {error && (
          <div className="card bg-red-50 border-2 border-red-200 mb-6 animate-slide-up">
            <p className="text-red-600 text-center font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* 메인 콘텐츠 */}
        {currentStep === 'upload' && (
          <UploadSection
            onImageSelect={handleImageSelect}
            selectedImage={selectedImage}
            onAnalyzeStart={handleAnalysisStart}
          />
        )}

        {currentStep === 'analyzing' && (
          <AnalysisSection />
        )}

        {currentStep === 'result' && (
          <ResultSection
            result={analysisResult}
            selectedImage={selectedImage}
            onReset={handleReset}
          />
        )}

        {/* 푸터 */}
        <footer className="text-center mt-12 text-gray-500 text-sm">
          <p>🥰 에겐: 귀엽고 차분한 스타일 | 💪 테토: 활동적이고 늠름한 스타일</p>
        </footer>
      </div>
    </div>
  )
}

export default App
