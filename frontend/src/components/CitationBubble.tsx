import { useState } from 'react';
import type { Citation } from '../types/api';

interface Props {
  content: string;
  citations: Citation[];
}

export default function CitationBubble({ content, citations }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  return (
    <div>
      <div className="whitespace-pre-wrap break-words text-sm">{content}</div>

      {citations.length > 0 && (
        <div className="mt-2 border-t border-gray-100 pt-2 space-y-1">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
            출처
          </p>
          {citations.map((c, i) => (
            <div key={i}>
              <button
                onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
              >
                <span className="bg-indigo-50 px-1.5 py-0.5 rounded font-mono text-[10px]">
                  REF {i + 1}
                </span>
                <span className="truncate max-w-[220px]">{c.source}</span>
                <span className="text-gray-400">p.{c.page}</span>
                {c.score !== null && (
                  <span className="text-gray-300 text-[10px]">
                    ({(c.score * 100).toFixed(0)}%)
                  </span>
                )}
              </button>

              {expandedIdx === i && (
                <div className="ml-6 mt-1 p-2 bg-gray-50 rounded-lg text-xs text-gray-600 leading-relaxed border border-gray-100">
                  {c.text}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
