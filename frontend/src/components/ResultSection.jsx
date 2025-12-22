export default function ResultSection({ result, selectedImage, onReset }) {
  const {
    classification,
    aegen_percentage,
    teto_percentage,
    comment,
    result_image,
    confidence = 50,
    confidence_level = '보통',
    models_agree = false,
    ensemble_info = {}
  } = result

  const isAegen = classification === 'aegen'
  const mainPercentage = isAegen ? aegen_percentage : teto_percentage
  const subPercentage = isAegen ? teto_percentage : aegen_percentage

  // 신뢰도 색상
  const getConfidenceColor = (conf) => {
    if (conf >= 90) return 'text-green-600'
    if (conf >= 75) return 'text-blue-600'
    if (conf >= 60) return 'text-yellow-600'
    if (conf >= 40) return 'text-orange-600'
    return 'text-red-600'
  }

  const getConfidenceBgColor = (conf) => {
    if (conf >= 90) return 'bg-green-50'
    if (conf >= 75) return 'bg-blue-50'
    if (conf >= 60) return 'bg-yellow-50'
    if (conf >= 40) return 'bg-orange-50'
    return 'bg-red-50'
  }

  const handleDownload = async () => {
    try {
      // fetch로 이미지를 blob으로 가져옴
      const response = await fetch(`http://localhost:5000/result/${result_image}`)
      const blob = await response.blob()

      // blob URL 생성 및 다운로드
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `pet-test-result-${Date.now()}.jpg`
      document.body.appendChild(link)
      link.click()

      // 정리
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('다운로드 실패:', error)
      alert('이미지 다운로드에 실패했습니다.')
    }
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: '반려동물 에겐 vs 테토 테스트 결과',
          text: `우리 아이는 ${isAegen ? '에겐' : '테토'} ${mainPercentage}%!`,
          url: window.location.href,
        })
      } catch (err) {
        console.log('공유 취소됨')
      }
    } else {
      alert('이 브라우저는 공유 기능을 지원하지 않습니다.')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 결과 카드 */}
      <div className="card">
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">
            {isAegen ? '🥰' : '💪'}
          </div>
          <h2 className="text-4xl font-bold mb-2">
            {isAegen ? (
              <span className="text-aegen">에겐</span>
            ) : (
              <span className="text-teto">테토</span>
            )}
          </h2>
          <p className="text-gray-600">
            {isAegen ? '귀엽고 사랑스러워요!' : '늠름하고 활동적이에요!'}
          </p>
        </div>

        {/* 퍼센티지 바 */}
        <div className="mb-6">
          <div className="flex justify-between text-sm font-semibold mb-2">
            <span className="text-aegen">에겐 {aegen_percentage}%</span>
            <span className="text-teto">테토 {teto_percentage}%</span>
          </div>
          <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="absolute left-0 h-full bg-gradient-to-r from-aegen to-aegen-light transition-all duration-1000 ease-out"
              style={{ width: `${aegen_percentage}%` }}
            ></div>
            <div
              className="absolute right-0 h-full bg-gradient-to-l from-teto to-teto-light transition-all duration-1000 ease-out"
              style={{ width: `${teto_percentage}%` }}
            ></div>
          </div>
        </div>

        {/* 코멘트 */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 mb-6">
          <p className="text-lg text-gray-800 leading-relaxed text-center">
            {comment}
          </p>
        </div>

        {/* 결과 이미지 */}
        {result_image && (
          <div className="mb-6 w-full overflow-auto">
            <img
              src={`http://localhost:5000/result/${result_image}?t=${new Date().getTime()}`}
              alt="결과"
              className="w-full h-auto rounded-xl shadow-lg"
              style={{ maxWidth: '100%', height: 'auto' }}
            />
          </div>
        )}

        {/* 액션 버튼들 */}
        <div className="flex flex-wrap gap-3 justify-center">
          <button
            onClick={handleDownload}
            className="btn-primary"
          >
            💾 이미지 다운로드
          </button>
          <button
            onClick={handleShare}
            className="btn-primary"
          >
            📱 공유하기
          </button>
          <button
            onClick={onReset}
            className="btn-secondary"
          >
            🔄 다시 테스트
          </button>
        </div>
      </div>

      {/* 상세 정보 */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-800 mb-4">
          📊 상세 분석
        </h3>

        {/* 신뢰도 정보 */}
        <div className={`${getConfidenceBgColor(confidence)} rounded-lg p-4 mb-4 border-2 ${confidence >= 75 ? 'border-green-200' : confidence >= 60 ? 'border-yellow-200' : 'border-orange-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 mb-1">AI 신뢰도</div>
              <div className={`text-2xl font-bold ${getConfidenceColor(confidence)}`}>
                {confidence.toFixed(1)}% ({confidence_level})
              </div>
            </div>
            <div className="text-right">
              {models_agree ? (
                <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                  ✓ 모델 일치
                </div>
              ) : (
                <div className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-semibold">
                  ⚠ 모델 불일치
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {ensemble_info.blip_prediction && ensemble_info.custom_prediction
                  ? `BLIP: ${ensemble_info.blip_prediction}, Custom: ${ensemble_info.custom_prediction}`
                  : 'Ensemble AI'}
              </p>
            </div>
          </div>
          {confidence < 60 && (
            <div className="mt-3 bg-white bg-opacity-50 rounded p-2">
              <p className="text-xs text-gray-700">
                💡 신뢰도가 낮습니다. 더 명확한 사진으로 다시 시도해보세요!
              </p>
            </div>
          )}
        </div>

        {/* 에겐/테토 지수 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-aegen-light bg-opacity-20 rounded-lg p-4">
            <div className="text-aegen font-bold text-lg mb-1">에겐 지수</div>
            <div className="text-3xl font-bold text-aegen">{aegen_percentage.toFixed(1)}%</div>
            <p className="text-sm text-gray-600 mt-2">귀엽고 차분한 정도</p>
            {ensemble_info.blip_aegen !== undefined && (
              <div className="mt-2 text-xs text-gray-500">
                <div>BLIP: {ensemble_info.blip_aegen?.toFixed(1)}%</div>
                <div>Custom: {ensemble_info.custom_aegen?.toFixed(1)}%</div>
              </div>
            )}
          </div>
          <div className="bg-teto-light bg-opacity-20 rounded-lg p-4">
            <div className="text-teto font-bold text-lg mb-1">테토 지수</div>
            <div className="text-3xl font-bold text-teto">{teto_percentage.toFixed(1)}%</div>
            <p className="text-sm text-gray-600 mt-2">활동적이고 늠름한 정도</p>
            {ensemble_info.blip_teto !== undefined && (
              <div className="mt-2 text-xs text-gray-500">
                <div>BLIP: {ensemble_info.blip_teto?.toFixed(1)}%</div>
                <div>Custom: {ensemble_info.custom_teto?.toFixed(1)}%</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
