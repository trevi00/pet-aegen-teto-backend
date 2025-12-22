import { useState, useRef } from 'react'

export default function UploadSection({ onImageSelect, selectedImage, onAnalyzeStart }) {
  const [isDragging, setIsDragging] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
      handleImageFile(file)
    }
  }

  const handleFileInput = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleImageFile(file)
    }
  }

  const handleImageFile = (file) => {
    onImageSelect(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreviewUrl(e.target.result)
    }
    reader.readAsDataURL(file)
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleCancel = () => {
    onImageSelect(null)
    setPreviewUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="card animate-slide-up">
      {!previewUrl ? (
        <div
          className={`upload-area ${isDragging ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <div className="text-6xl mb-4">📸</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            이미지를 드래그하거나 클릭하여 업로드
          </h3>
          <p className="text-gray-500 mb-4">
            JPG, PNG 파일 지원
          </p>
          <button className="btn-primary inline-block">
            파일 선택
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      ) : (
        <div className="animate-fade-in">
          <div className="mb-6">
            <img
              src={previewUrl}
              alt="미리보기"
              className="max-w-full max-h-96 mx-auto rounded-xl shadow-lg"
            />
          </div>
          <div className="flex gap-4 justify-center">
            <button
              onClick={onAnalyzeStart}
              className="btn-primary"
            >
              🔍 분석 시작하기
            </button>
            <button
              onClick={handleCancel}
              className="btn-secondary"
            >
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
