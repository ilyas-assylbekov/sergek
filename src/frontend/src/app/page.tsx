import { UploadZone } from '@/components/video/upload-zone'

export const dynamic = 'force-static'
export const revalidate = false

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto p-6">
        <div className="text-center mb-12 pt-8">
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 mb-4 leading-relaxed">
            Sergek Road Incident Detection
          </h1>
        </div>
        <div className="max-w-4xl mx-auto">
          <UploadZone />
        </div>
      </div>
    </main>
  )
}