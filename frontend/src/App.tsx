import React, { useState, useEffect, useRef } from 'react';

interface AppConfig {
  models: string[];
  max_file_size_mb: number;
  max_duration_minutes: number;
}

function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [model, setModel] = useState('base');
  const [language, setLanguage] = useState('auto');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Fetch configuration from API
    fetch('http://localhost:8000/api/config')
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error("Error fetching config:", err));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Selecione um arquivo de mídia primeiro!");
      return;
    }
    console.log("Starting upload:", {
      file: selectedFile.name,
      model,
      language
    });
    alert("Upload iniciado! (Integração na próxima etapa)");
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
        
        {/* Header */}
        <div className="bg-indigo-600 px-6 py-8 text-white text-center">
          <h1 className="text-3xl font-bold">Escreve.AI</h1>
          <p className="mt-2 text-indigo-100">Transcreva seus áudios e vídeos localmente com IA</p>
        </div>

        {/* Form Content */}
        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Drag & Drop Zone */}
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:bg-gray-50 transition cursor-pointer"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-4 text-sm text-gray-600">
                <span className="font-medium text-indigo-600 hover:text-indigo-500">Clique para selecionar</span> ou arraste um arquivo aqui
              </p>
              <p className="mt-1 text-xs text-gray-500">
                MP3, MP4, WAV, OGG, M4A, AAC
              </p>
              {selectedFile && (
                <div className="mt-4 p-3 bg-indigo-50 rounded-md text-indigo-800 font-medium break-all">
                  📄 {selectedFile.name}
                </div>
              )}
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept="audio/*,video/*"
                onChange={handleFileChange}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Language Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Idioma do Áudio</label>
                <select 
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="auto">Automático (Detectar)</option>
                  <option value="pt">Português (Brasil)</option>
                  <option value="en">Inglês</option>
                  <option value="es">Espanhol</option>
                </select>
              </div>

              {/* Model Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Modelo de IA</label>
                <select 
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  {config?.models ? (
                    config.models.map(m => (
                      <option key={m} value={m}>{m} {m === 'base' ? '(Recomendado)' : ''}</option>
                    ))
                  ) : (
                    <option value="base">base (Carregando...)</option>
                  )}
                </select>
              </div>
            </div>

            {config && (
              <div className="text-xs text-gray-500">
                Limites do sistema: {config.max_file_size_mb}MB | {config.max_duration_minutes} minutos
              </div>
            )}

            <button 
              type="submit"
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Começar Transcrição
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
