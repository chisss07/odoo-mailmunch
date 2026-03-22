interface EmailViewerProps {
  email: {
    sender: string
    subject: string
    body_text: string
    body_html?: string
    attachment_paths?: string[]
  }
}

function basename(path: string): string {
  return path.split(/[\\/]/).pop() ?? path
}

export default function EmailViewer({ email }: EmailViewerProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="bg-surface-light rounded-t-lg px-4 py-3 border-b border-white/10">
        <h2 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
          Original Email
        </h2>
        <div className="space-y-1">
          <div className="flex gap-2 text-sm">
            <span className="text-white/40 w-14 flex-shrink-0">From</span>
            <span className="text-white/80 truncate">{email.sender}</span>
          </div>
          <div className="flex gap-2 text-sm">
            <span className="text-white/40 w-14 flex-shrink-0">Subject</span>
            <span className="text-white font-medium">{email.subject}</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-surface-light rounded-b-lg">
        {email.body_html ? (
          <div
            className="p-4 text-sm text-white/80 [&_a]:text-primary [&_a]:underline prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: email.body_html }}
          />
        ) : (
          <pre className="p-4 text-sm text-white/80 whitespace-pre-wrap font-mono leading-relaxed">
            {email.body_text}
          </pre>
        )}
      </div>

      {email.attachment_paths && email.attachment_paths.length > 0 && (
        <div className="mt-3 bg-surface-light rounded-lg p-3">
          <p className="text-white/40 text-xs uppercase tracking-wider mb-2">Attachments</p>
          <ul className="space-y-1">
            {email.attachment_paths.map((path, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-white/70">
                <svg
                  className="w-3.5 h-3.5 text-white/30 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                  />
                </svg>
                <span className="truncate">{basename(path)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
