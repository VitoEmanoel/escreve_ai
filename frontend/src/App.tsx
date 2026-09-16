import React, { useState, useEffect, useRef } from 'react';
import { JobItem, type JobData } from './components/JobItem';

interface AppConfig {
  models: string[];
  max_file_size_mb: number;
  max_duration_minutes: number;
}

function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [model, setModel] = useState('base');
  const [language, setLanguage] = useState('auto');
  const [taskMethod, setTaskMethod] = useState('transcribe');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [inputMode, setInputMode] = useState<'file' | 'youtube'>('file');
  
  const [activeJobs, setActiveJobs] = useState<JobData[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error("Error fetching config:", err));
  }, []);

  const processFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    const validFiles = Array.from(files).filter(file => {
      // Verifica se é áudio ou vídeo
      if (!file.type.startsWith('audio/') && !file.type.startsWith('video/') && !file.name.match(/\.(mkv|mp4|webm|wav|mp3|m4a|ogg|flac)$/i)) {
        console.warn(`Arquivo ignorado (não suportado): ${file.name}`);
        return false;
      }
      return true;
    });

    if (validFiles.length === 0) return;

    setSelectedFiles(prev => {
      const newFiles: File[] = [];
      for (const file of validFiles) {
        // Verifica se já não existe um arquivo com mesmo nome e tamanho
        const isDuplicate = prev.some(existing => existing.name === file.name && existing.size === file.size);
        if (!isDuplicate) {
          newFiles.push(file);
        }
      }
      return [...prev, ...newFiles];
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    processFiles(e.dataTransfer.files);
  };

  const removeSelectedFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMode === 'file' && selectedFiles.length === 0) return;
    if (inputMode === 'youtube' && !youtubeUrl) return;

    setIsUploading(true);
    
    try {
      if (inputMode === 'youtube') {
        const formData = new FormData();
        formData.append('youtube_url', youtubeUrl);
        formData.append('language', language);
        formData.append('model', model);
        formData.append('task', taskMethod);

        const res = await fetch('/api/jobs', { method: 'POST', body: formData });
        const data = await res.json();
        
        if (!res.ok) {
          alert(`Erro: ${data.detail || 'Falha no upload'}`);
        } else {
          setActiveJobs(prev => [data, ...prev]);
          setYoutubeUrl('');
        }
      } else {
        // Enviar multiplos arquivos em lote
        const newJobs: JobData[] = [];
        for (const file of selectedFiles) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('language', language);
          formData.append('model', model);
          formData.append('task', taskMethod);

          const res = await fetch('/api/jobs', { method: 'POST', body: formData });
          const data = await res.json();
          if (res.ok) {
            newJobs.push(data);
          } else {
            console.error(`Erro ao enviar ${file.name}:`, data);
          }
        }
        setActiveJobs(prev => [...newJobs, ...prev]);
        setSelectedFiles([]);
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Erro ao enviar arquivos.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleJobDelete = (deletedId: string) => {
    setActiveJobs(prev => prev.filter(job => job.id !== deletedId));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="bg-indigo-600 px-6 py-8 text-white text-center">
            <div className="flex justify-center items-center space-x-1">
              <img src="/logobranca.png" alt="Logo" className="h-14 w-auto" />
              <h1 className="text-4xl font-bold">Escreve.AI</h1>
            </div>
            <p className="mt-2 text-indigo-100">Transcreva seus áudios e vídeos localmente com IA</p>
          </div>

          <div className="p-8">
            <div className="flex justify-center space-x-4 mb-6">
              <button
                type="button"
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${inputMode === 'file' ? 'bg-indigo-600 text-white shadow' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                onClick={() => setInputMode('file')}
              >
                Upload de Arquivo
              </button>
              <button
                type="button"
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${inputMode === 'youtube' ? 'bg-indigo-600 text-white shadow' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                onClick={() => setInputMode('youtube')}
              >
                Link do YouTube
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {inputMode === 'file' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Arquivos de Mídia</label>
                  <div 
                    className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-indigo-500 transition-colors"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                  >
                    <div className="space-y-1 text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div className="flex text-sm text-gray-600 justify-center">
                        <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                          <span>Selecione os arquivos</span>
                          <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} ref={fileInputRef} accept="audio/*,video/*,.mkv,.mp4,.webm,.wav,.mp3,.m4a,.ogg,.flac" multiple />
                        </label>
                        <p className="pl-1">ou arraste para cá</p>
                      </div>
                      <p className="text-xs text-gray-500">
                        MP3, WAV, MP4, MKV até {config?.max_file_size_mb || 500}MB
                      </p>
                    </div>
                  </div>
                  
                  {selectedFiles.length > 0 && (
                    <div className="mt-4 bg-gray-50 p-4 rounded-md border border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Arquivos selecionados ({selectedFiles.length})</h4>
                      <ul className="space-y-2">
                        {selectedFiles.map((file, idx) => (
                          <li key={idx} className="flex justify-between items-center text-sm text-gray-600 bg-white px-3 py-2 rounded shadow-sm">
                            <span className="truncate">{file.name}</span>
                            <button 
                              type="button" 
                              onClick={() => removeSelectedFile(idx)}
                              className="text-red-500 hover:text-red-700 ml-2 shrink-0"
                            >
                              X
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label htmlFor="youtube_url" className="block text-sm font-medium text-gray-700">URL do Vídeo</label>
                  <input
                    type="url"
                    name="youtube_url"
                    id="youtube_url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                  />
                  <p className="mt-1 text-xs text-gray-500">O áudio será baixado diretamente do YouTube.</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="task" className="block text-sm font-medium text-gray-700">Ação</label>
                  <select
                    id="task"
                    name="task"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    value={taskMethod}
                    onChange={(e) => setTaskMethod(e.target.value)}
                  >
                    <option value="transcribe">Transcrever</option>
                    <option value="translate">Traduzir (para Inglês)</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-gray-700">Idioma do Áudio</label>
                  <select
                    id="language"
                    name="language"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="auto">Detectar Automático</option>
                    <option value="pt">Português</option>
                    <option value="en">Inglês</option>
                    <option value="es">Espanhol</option>
                    <option value="fr">Francês</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="model" className="block text-sm font-medium text-gray-700">Tamanho do Modelo</label>
                  <select
                    id="model"
                    name="model"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                  >
                    {config?.models.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isUploading || (inputMode === 'file' && selectedFiles.length === 0) || (inputMode === 'youtube' && !youtubeUrl)}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {isUploading ? 'Iniciando Lote...' : 'Começar Transcrição'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Fila de Jobs */}
        {activeJobs.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-800 border-b pb-2">Tarefas ({activeJobs.length})</h2>
            <div className="grid grid-cols-1 gap-4">
              {activeJobs.map(job => (
                <JobItem key={job.id} initialJob={job} onDelete={handleJobDelete} />
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
