import { useState, useEffect } from 'react';

export interface JobData {
  id: string;
  original_filename?: string;
  status: string;
  progress: number;
  error_message?: string;
  full_text?: string;
  diarize?: boolean;
  segments?: any[];
}

interface JobItemProps {
  initialJob: JobData;
  onDelete: (id: string) => void;
}

export function JobItem({ initialJob, onDelete }: JobItemProps) {
  const [job, setJob] = useState<JobData>(initialJob);
  const [searchTerm, setSearchTerm] = useState('');

  // WebSocket Hook
  useEffect(() => {
    let ws: WebSocket | null = null;

    if (job.status === 'queued' || job.status === 'processing') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/ws/jobs/${job.id}`;
      
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            console.error("WS Error:", data.error);
            return;
          }
          setJob(data as JobData);
        } catch (err) {
          console.error("Failed to parse WS message:", err);
        }
      };
    }

    return () => {
      if (ws) ws.close();
    };
  }, [job.id, job.status]);

  const handleDelete = async () => {
    if (!confirm("Tem certeza que deseja excluir os dados desta transcrição?")) return;
    try {
      await fetch(`/api/jobs/${job.id}`, { method: 'DELETE' });
      onDelete(job.id);
    } catch (error) {
      console.error("Delete error:", error);
      alert("Erro ao excluir o job.");
    }
  };

  const highlightText = (text: string, highlight: string) => {
    if (!highlight.trim()) return text;
    const parts = text.split(new RegExp(`(${highlight})`, 'gi'));
    return (
      <span>
        {parts.map((part, i) => 
          part.toLowerCase() === highlight.toLowerCase() ? (
            <mark key={i} className="bg-yellow-200 text-yellow-900 rounded-sm">{part}</mark>
          ) : (
            part
          )
        )}
      </span>
    );
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
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-800 truncate" title={job.original_filename}>
          {job.original_filename || 'Transcrição'}
        </h3>
        <button 
          onClick={handleDelete}
          className="text-red-500 hover:text-red-700 text-sm font-medium"
        >
          Remover
        </button>
      </div>

      <div className="space-y-4">
        <div className="text-sm">
          Status: <span className="text-indigo-600 font-medium">{translateStatus(job.status)}</span>
          {job.error_message && (
            <p className="mt-1 text-red-600">{job.error_message}</p>
          )}
        </div>
        
        <div className="relative pt-1">
          <div className="flex mb-1 items-center justify-between">
            <div>
              <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-600 bg-indigo-100">
                Progresso
              </span>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold inline-block text-indigo-600">
                {job.progress}%
              </span>
            </div>
          </div>
          <div className="overflow-hidden h-2 mb-2 text-xs flex rounded bg-indigo-100">
            <div style={{ width: `${job.progress}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-500 transition-all duration-500 ease-in-out"></div>
          </div>
        </div>

        {job.status === 'completed' && (
          <div className="mt-4 space-y-4">
            {(job.diarize && job.segments) ? (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center gap-2">
                  <h4 className="font-medium text-gray-700 text-sm whitespace-nowrap">Diálogo Transcrito</h4>
                  <input 
                    type="text" 
                    placeholder="Pesquisar..." 
                    className="w-full max-w-[200px] px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="p-3 bg-white max-h-60 overflow-y-auto text-gray-800 text-sm space-y-2">
                  {job.segments.map((seg: any, i: number) => (
                    <div key={i} className="mb-2">
                      <span className="font-bold text-indigo-600 mr-2">{seg.speaker || 'Locutor'}:</span>
                      <span>{highlightText(seg.text, searchTerm)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : job.full_text ? (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center gap-2">
                  <h4 className="font-medium text-gray-700 text-sm whitespace-nowrap">Texto Transcrito</h4>
                  <input 
                    type="text" 
                    placeholder="Pesquisar..." 
                    className="w-full max-w-[200px] px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="p-3 bg-white max-h-40 overflow-y-auto text-gray-800 text-sm whitespace-pre-wrap">
                  {highlightText(job.full_text, searchTerm)}
                </div>
              </div>
            ) : null}

            <div>
              <div className="flex flex-wrap gap-2 mt-2">
                <a href={`/api/jobs/${job.id}/download?format=txt`} className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition">TXT</a>
                <a href={`/api/jobs/${job.id}/download?format=srt`} className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition">SRT (Legenda)</a>
                <a href={`/api/jobs/${job.id}/download?format=vtt`} className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition">VTT (Legenda Web)</a>
                <a href={`/api/jobs/${job.id}/download?format=json`} className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition">JSON</a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
