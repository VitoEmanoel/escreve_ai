import React, { useState, useEffect, useRef } from 'react';

interface AppConfig {
  models: string[];
  max_file_size_mb: number;
  max_duration_minutes: number;
}

interface JobData {
  id: string;
  status: string;
  progress: number;
  error_message?: string;
}

function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [model, setModel] = useState('base');
  const [language, setLanguage] = useState('auto');
  
  const [activeJob, setActiveJob] = useState<JobData | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/config')
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error("Error fetching config:", err));
  }, []);

  // Polling hook
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (activeJob && (activeJob.status === 'queued' || activeJob.status === 'processing')) {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/jobs/${activeJob.id}`);
          if (res.ok) {
            const data: JobData = await res.json();
            setActiveJob(data);
          }
        } catch (error) {
          console.error("Error polling job status:", error);
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [activeJob]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('language', language);
    formData.append('model', model);
    formData.append('task', 'transcribe');

    try {
      const res = await fetch('http://localhost:8000/api/jobs', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        alert(`Erro: ${data.detail || 'Falha no upload'}`);
        setIsUploading(false);
        return;
      }

      setActiveJob(data);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Erro ao enviar o arquivo.");
    } finally {
      setIsUploading(false);
    }
  };

  const translateStatus = (status: string) => {
    switch (status) {
      case 'queued': return 'Na fila...';
      case 'processing': return 'Processando...';
      case 'completed': return 'Concluído!';
      case 'failed': return 'Falhou';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
        
        <div className="bg-indigo-600 px-6 py-8 text-white text-center">
          <h1 className="text-3xl font-bold">Escreve.AI</h1>
          <p className="mt-2 text-indigo-100">Transcreva seus áudios e vídeos localmente com IA</p>
        </div>

        <div className="p-8">
          {activeJob ? (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-xl font-medium text-gray-900">
                  Status: <span className="text-indigo-600">{translateStatus(activeJob.status)}</span>
                </h3>
                {activeJob.error_message && (
                  <p className="mt-2 text-sm text-red-600">{activeJob.error_message}</p>
                )}
              </div>
              
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-600 bg-indigo-200">
                      Progresso
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-indigo-600">
                      {activeJob.progress}%
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-indigo-200">
                  <div style={{ width: `${activeJob.progress}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-600 transition-all duration-500 ease-in-out"></div>
                </div>
              </div>

              {activeJob.status === 'completed' && (
                <div className="text-center">
                  <p className="text-green-600 font-medium">Transcrição finalizada! (Exibição de resultados na próxima etapa)</p>
                  <button 
                    onClick={() => { setActiveJob(null); setSelectedFile(null); }}
                    className="mt-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700"
                  >
                    Fazer nova transcrição
                  </button>
                </div>
              )}
              {activeJob.status === 'failed' && (
                <div className="text-center">
                  <button 
                    onClick={() => { setActiveJob(null); }}
                    className="mt-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
                  >
                    Tentar Novamente
                  </button>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              
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
                disabled={!selectedFile || isUploading}
                className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${(!selectedFile || isUploading) ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'}`}
              >
                {isUploading ? 'Enviando arquivo...' : 'Começar Transcrição'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
