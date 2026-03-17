import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type {
  Tenant,
  DocumentMeta,
  AvailableFile,
  IngestResponse,
} from '../types/api';

export default function DocumentsScreen() {
  const navigate = useNavigate();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState('default');
  const [docs, setDocs] = useState<DocumentMeta[]>([]);
  const [files, setFiles] = useState<AvailableFile[]>([]);
  const [ingesting, setIngesting] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);

  useEffect(() => {
    fetch('/api/tenants').then((r) => r.json()).then(setTenants).catch(console.error);
    fetch('/api/ingest/files').then((r) => r.json()).then(setFiles).catch(console.error);
  }, []);

  useEffect(() => {
    fetch(`/api/documents?tenant_id=${tenantId}`)
      .then((r) => r.json())
      .then(setDocs)
      .catch(console.error);
  }, [tenantId]);

  const runIngest = async () => {
    setIngesting(true);
    setResult(null);
    try {
      const resp = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      const data: IngestResponse = await resp.json();
      setResult(data);
      // Refresh docs list
      const docsResp = await fetch(`/api/documents?tenant_id=${tenantId}`);
      setDocs(await docsResp.json());
    } catch (e) {
      setResult({ status: 'error', ingested: 0, documents: [] });
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex flex-col bg-gray-900 text-white shrink-0">
        <div className="px-4 py-4">
          <h1 className="text-base font-bold tracking-tight">HK Chatbot</h1>
          <p className="text-[10px] text-gray-400 mt-0.5">문서 관리</p>
        </div>

        <div className="px-3 pb-3">
          <label className="text-[10px] text-gray-500 uppercase tracking-wide block mb-1">
            테넌트
          </label>
          <select
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="w-full bg-gray-800 text-xs text-white border border-gray-700 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1" />

        <div className="p-3 border-t border-gray-700 space-y-1">
          <button
            onClick={() => navigate('/chat')}
            className="w-full text-left px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            💬 채팅으로
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shrink-0">
          <span className="text-sm font-medium text-gray-700">문서 관리</span>
          <button
            onClick={runIngest}
            disabled={ingesting}
            className="px-4 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {ingesting ? '인덱싱 중…' : '전체 인덱싱 시작'}
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Result banner */}
          {result && (
            <div
              className={`p-3 rounded-xl text-sm ${
                result.status === 'ok'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {result.status === 'ok'
                ? `✓ ${result.ingested}개 문서, ${result.total_nodes}개 청크 인덱싱 완료`
                : `인덱싱 실패: ${result.status}`}
            </div>
          )}

          {/* Ingested documents */}
          <section>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              인덱싱된 문서 ({docs.length})
            </h2>
            {docs.length === 0 ? (
              <div className="text-center py-12 text-gray-400 text-sm">
                인덱싱된 문서가 없습니다. "전체 인덱싱 시작" 버튼을 눌러주세요.
              </div>
            ) : (
              <div className="space-y-2">
                {docs.map((doc) => (
                  <div
                    key={doc.filename}
                    className="bg-white rounded-xl p-4 shadow-sm border border-gray-100"
                  >
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-medium text-gray-800 truncate">
                          {doc.title}
                        </h3>
                        <p className="text-xs text-gray-400 mt-0.5 truncate">
                          {doc.filename}
                        </p>
                      </div>
                      <span className="ml-3 shrink-0 text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded">
                        {doc.page_count}p
                      </span>
                    </div>
                    {doc.summary && (
                      <p className="mt-2 text-xs text-gray-500 line-clamp-2 leading-relaxed">
                        {doc.summary}
                      </p>
                    )}
                    {doc.ingested_at && (
                      <p className="mt-1 text-[10px] text-gray-300">
                        인덱싱: {new Date(doc.ingested_at).toLocaleString('ko-KR')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Available files */}
          <section>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              data/ 디렉토리 파일 ({files.length})
            </h2>
            <div className="space-y-1">
              {files.map((f) => (
                <div
                  key={f.filename}
                  className="flex items-center justify-between px-3 py-2 bg-white rounded-lg border border-gray-100 text-sm"
                >
                  <span className="truncate text-gray-700 text-xs">{f.filename}</span>
                  <span className="text-xs text-gray-400 shrink-0 ml-2">
                    {f.size_mb} MB
                  </span>
                </div>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
