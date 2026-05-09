import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import api from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/store/authStore'
import {
  MessageCircle,
  Send,
  ImagePlus,
  FileText,
  // X,
} from 'lucide-react'
import type { components } from '@/types/api'

type Job = components['schemas']['JobOut']
type Message = components['schemas']['MessageOut']

// Cloudinary image upload helper
async function uploadFile(file: File): Promise<string> {
  const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
  const preset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET
  const formData = new FormData()
  formData.append('file', file)
  formData.append('upload_preset', preset)
  const res = await fetch(
    `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`,
    { method: 'POST', body: formData }
  )
  const data = await res.json()
  if (!res.ok) {
    toast.error('Upload failed: ' + (data.error?.message || ''))
    throw new Error(data.error?.message || 'Upload failed')
  }
  toast.success('Image uploaded')
  return data.secure_url
}

const statusBadge = (status: string) => {
  switch (status) {
    case 'open':
      return <Badge className="bg-blue-100 text-blue-800">Open</Badge>
    case 'assigned':
      return <Badge className="bg-yellow-100 text-yellow-800">Assigned</Badge>
    case 'funded':
      return <Badge className="bg-green-100 text-green-800">Funded</Badge>
    case 'in_progress':
      return <Badge className="bg-purple-100 text-purple-800">In Progress</Badge>
    case 'completed':
      return <Badge className="bg-black text-white">Completed</Badge>
    case 'cancelled':
      return <Badge className="bg-red-100 text-red-800">Canceled</Badge>
    default:
      return <Badge>{status}</Badge>
  }
}

export default function MessagesPage() {
  const { user } = useAuthStore()
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [messageText, setMessageText] = useState('')
  const [showScopeAmend, setShowScopeAmend] = useState(false)
  const [amendReason, setAmendReason] = useState('')
  const [amendNewPrice, setAmendNewPrice] = useState('')
  const [amendImage, setAmendImage] = useState<File | null>(null)
  const [amendImagePreview, setAmendImagePreview] = useState<string | null>(null)

  // Fetch all my jobs that are active (for the sidebar)
  const { data: myJobs, isLoading: jobsLoading } = useQuery<Job[]>({
    queryKey: ['myJobsForMessages'],
    queryFn: async () => {
      const [c, p] = await Promise.all([
        api.get('/jobs/', { params: { my: 'client' } }),
        api.get('/jobs/', { params: { my: 'provider' } }),
      ])
      return [...c.data, ...p.data]
    },
  })

  const activeJobs =
    myJobs?.filter(
      (j) => !['completed', 'cancelled'].includes(j.status)
    ) || []

  // Messages for the selected job
  const {
    data: messages,
    isLoading: msgsLoading,
    refetch,
  } = useQuery<Message[]>({
    queryKey: ['messages', selectedJob?.id],
    queryFn: async () => {
      if (!selectedJob?.id) return []
      const { data } = await api.get(`/messages/job/${selectedJob.id}`)
      return data
    },
    enabled: !!selectedJob?.id,
    refetchInterval: 5000,
  })

  const { data: amendments } = useQuery({
    queryKey: ['amendments', selectedJob?.id],
    queryFn: async () => {
      if (!selectedJob?.id) return []
      const { data } = await api.get(`/amendments/${selectedJob.id}`)
      return data
    },
    enabled: !!selectedJob?.id,
  })

  // Send text message
  const sendTextMutation = useMutation({
    mutationFn: async () => {
      if (!selectedJob?.id || !messageText.trim()) return
      await api.post('/messages/', {
        job_id: selectedJob.id,
        content: messageText,
      })
    },
    onSuccess: () => {
      refetch()
      setMessageText('')
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail || 'Message failed'),
  })

  // Send image message
  const sendImageMutation = useMutation({
    mutationFn: async (file: File) => {
      const url = await uploadFile(file)
      if (!selectedJob?.id) return
      await api.post('/messages/', {
        job_id: selectedJob.id,
        content: url, // send image URL as message content
      })
    },
    onSuccess: () => {
      refetch()
      toast.success('Image sent')
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail || 'Image send failed'),
  })

  // Scope amendment
  const scopeAmendMutation = useMutation({
    mutationFn: async () => {
      if (!selectedJob?.id || !amendReason || !amendNewPrice) return
      let imageUrl: string | undefined
      if (amendImage) {
        imageUrl = await uploadFile(amendImage)
      }
      await api.post(`/amendments/${selectedJob.id}`, {
        proposed_by: 'provider',
        reason: amendReason,
        new_total_price: amendNewPrice,
        additional_cost: '0',
        image_url: imageUrl,
      })
    },
    onSuccess: () => {
      toast.success('Scope amendment proposed')
      setShowScopeAmend(false)
      setAmendReason('')
      setAmendNewPrice('')
      setAmendImage(null)
      setAmendImagePreview(null)
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail || 'Amendment failed'),
  })

  const handleSendMessage = () => {
    if (!messageText.trim()) return
    sendTextMutation.mutate()
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      sendImageMutation.mutate(file)
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold">Messages</h1>
        <p className="text-gray-500">
          Contract rooms for your active jobs
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Sidebar with job list */}
        <div className="md:col-span-1 space-y-2">
          {jobsLoading ? (
            <Skeleton className="h-12 w-full" />
          ) : activeJobs.length === 0 ? (
            <p className="text-sm text-gray-500">
              No active jobs with messages.
            </p>
          ) : (
            activeJobs.map((job) => (
              <Card
                key={job.id}
                className={`cursor-pointer hover:shadow-md transition-shadow ${
                  selectedJob?.id === job.id
                    ? 'border-black'
                    : 'border-gray-100'
                }`}
                onClick={() => {
                  setSelectedJob(job)
                  setShowScopeAmend(false) // reset amendment view
                }}
              >
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {job.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {statusBadge(job.status)}
                      </p>
                    </div>
                    {job.image_url && (
                      <img
                        src={job.image_url}
                        className="w-10 h-10 rounded-lg object-cover ml-2 flex-shrink-0"
                      />
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Chat area */}
        <div className="md:col-span-2">
          {!selectedJob ? (
            <div className="text-center py-12 text-gray-500">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Select a job to open its contract room</p>
            </div>
          ) : (
            <Card className="flex flex-col h-[60vh]">
              <CardHeader className="border-b">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">
                    {selectedJob.title}
                  </CardTitle>
                  {statusBadge(selectedJob.status)}
                </div>
                {selectedJob.escrow_address && (
                  <p className="text-xs text-green-600 mt-1">
                    Escrow: {selectedJob.escrow_address.slice(0, 8)}...
                  </p>
                )}
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto space-y-3 py-4">
                {msgsLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : messages?.length ? (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${
                        msg.sender_id === user?.id
                          ? 'justify-end'
                          : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[75%] rounded-lg p-3 ${
                          msg.sender_id === user?.id
                            ? 'bg-black text-white'
                            : 'bg-gray-100 text-black'
                        }`}
                      >
                        {/* If message is an image URL, display image */}
                        {msg.content.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp)(\?.*)?$/i) ? (
                          <a href={msg.content} target="_blank" rel="noopener noreferrer">
                            <img
                              src={msg.content}
                              alt="sent image"
                              className="rounded-lg max-w-full max-h-60 object-cover cursor-pointer"
                            />
                          </a>
                        ) : (
                          <p className="text-sm">{msg.content}</p>
                        )}
                        <span className="text-xs opacity-70">
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-gray-500 text-sm">
                    No messages yet. Start the conversation.
                  </p>
                )}

                {/* Inline amendment proposal display */}
                {/* {selectedJob?.scope_amendments?.map((am: any) => (
                  <div
                    key={am.id}
                    className="flex justify-center"
                  >
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-[85%] text-sm">
                      <p className="font-medium">
                        Scope Amendment Proposed
                      </p>
                      <p>{am.reason}</p>
                      <p className="font-semibold">
                        New price: ₦
                        {parseFloat(
                          am.new_total_price as string
                        ).toLocaleString()}
                      </p>
                      {am.image_url && (
                        <img
                          src={am.image_url}
                          className="rounded-lg w-20 h-20 object-cover mt-1"
                        />
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {am.is_accepted === null
                          ? 'Pending'
                          : am.is_accepted
                          ? 'Accepted'
                          : 'Rejected'}
                      </p>
                    </div>
                  </div>
                ))} */}
                {amendments?.map((am: any) => (
                  <div key={am.id} className="flex justify-center">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-[85%] text-sm">
                      <p className="font-medium">Scope Amendment Proposed</p>
                      <p>{am.reason}</p>
                      <p className="font-semibold">
                        New price: ₦{parseFloat(am.new_total_price as string).toLocaleString()}
                      </p>
                      {am.image_url && (
                        <img src={am.image_url} className="rounded-lg w-20 h-20 object-cover mt-1" />
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {am.is_accepted === null ? 'Pending' : am.is_accepted ? 'Accepted' : 'Rejected'}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>

              {/* Input area */}
              {!showScopeAmend ? (
                <div className="border-t p-3 flex gap-2 items-center">
                  <label className="cursor-pointer">
                    <ImagePlus className="w-5 h-5 text-gray-500 hover:text-black" />
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageSelect}
                    />
                  </label>
                  <Input
                    placeholder="Type a message..."
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSendMessage()
                    }}
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    onClick={handleSendMessage}
                    disabled={!messageText.trim()}
                    className="bg-black text-white"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowScopeAmend(true)}
                  >
                    <FileText className="w-4 h-4 mr-1" /> Amend
                  </Button>
                </div>
              ) : (
                <div className="border-t p-3 space-y-2">
                  <Textarea
                    placeholder="Reason for amendment..."
                    value={amendReason}
                    onChange={(e) => setAmendReason(e.target.value)}
                  />
                  <Input
                    placeholder="New total price"
                    type="number"
                    value={amendNewPrice}
                    onChange={(e) => setAmendNewPrice(e.target.value)}
                  />
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        document
                          .getElementById('msgAmendImage')
                          ?.click()
                      }
                    >
                      <ImagePlus className="w-4 h-4 mr-1" /> Attach
                      Image
                    </Button>
                    <input
                      id="msgAmendImage"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) {
                          setAmendImage(file)
                          setAmendImagePreview(
                            URL.createObjectURL(file)
                          )
                        }
                      }}
                    />
                    {amendImagePreview && (
                      <img
                        src={amendImagePreview}
                        className="w-12 h-12 rounded-lg object-cover"
                      />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => scopeAmendMutation.mutate()}
                      disabled={!amendReason || !amendNewPrice}
                      className="bg-black text-white"
                    >
                      Submit Amendment
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowScopeAmend(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}