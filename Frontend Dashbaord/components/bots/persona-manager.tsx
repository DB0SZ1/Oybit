"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { type BotId } from "@/lib/bot-config"
import { UserCircle, Loader2, Sparkles, CheckCircle2 } from "lucide-react"
import { useBotData } from "@/hooks/use-bot-data"
import { ApiClient } from "@/lib/api-client"

interface Question {
  id: string
  layer: number
  question: string
  hint: string
}

interface OnboardingData {
  published_post_count: number
  total_questions: number
  available_questions: number
  answered_count: number
  core_complete: boolean
  core_answered: number
  next_questions: Question[]
}

export function PersonaManager({ botId }: { botId: BotId }) {
  const { data: activeData, loading: activeLoading, mutate: mutateActive } = useBotData<{ active?: { markdown?: string }, needs_onboarding?: boolean }>(botId, "api/personas/active")
  const { data: onboardingData, loading: onboardingLoading, mutate: mutateOnboarding } = useBotData<OnboardingData>(botId, "api/personas/onboarding")
  
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [savingId, setSavingId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleSaveAnswer = async (questionId: string) => {
    const answer = answers[questionId]
    if (!answer?.trim()) return

    try {
      setSavingId(questionId)
      await ApiClient.fetchBot(botId, "api/personas/onboarding/answer", {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, answer })
      })
      await mutateOnboarding()
    } catch (err) {
      console.error("Failed to save answer", err)
    } finally {
      setSavingId(null)
    }
  }

  const handleGeneratePersona = async () => {
    try {
      setIsGenerating(true)
      await ApiClient.fetchBot(botId, "api/personas/onboarding/generate", {
        method: "POST"
      })
      await mutateActive()
      await mutateOnboarding()
    } catch (err) {
      console.error("Failed to generate persona", err)
    } finally {
      setIsGenerating(false)
    }
  }

  if (activeLoading || onboardingLoading) {
    return (
      <Card>
        <CardContent className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  // If a persona already exists, just show it
  if (activeData?.active?.markdown && !activeData?.needs_onboarding) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <UserCircle className="h-5 w-5 text-primary" />
            <CardTitle>Active Persona</CardTitle>
          </div>
          <CardDescription>Your generated digital brain based on the 60 questions.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-muted/30 p-4 rounded-md overflow-y-auto max-h-[500px]">
            <pre className="text-sm text-foreground whitespace-pre-wrap font-mono">
              {activeData.active.markdown}
            </pre>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Otherwise, show the Onboarding Wizard
  return (
    <Card className="border-primary/20">
      <CardHeader className="bg-primary/5 border-b">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <CardTitle>Persona Training Wizard</CardTitle>
        </div>
        <CardDescription>
          Answer the core 10 questions to synthesize your digital brain. 
          Progress: {onboardingData?.core_answered || 0} / 10 Core Questions Answered
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-6 space-y-8">
        {onboardingData?.next_questions?.map((q) => (
          <div key={q.id} className="space-y-3 bg-muted/20 p-4 rounded-lg border">
            <div>
              <h4 className="font-medium text-foreground">{q.question}</h4>
              <p className="text-sm text-muted-foreground mt-1">Hint: {q.hint}</p>
            </div>
            <div className="flex gap-2">
              <Textarea 
                placeholder="Type your answer..."
                className="min-h-[80px]"
                value={answers[q.id] || ""}
                onChange={(e) => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
              />
            </div>
            <div className="flex justify-end">
              <Button 
                size="sm" 
                variant="secondary"
                onClick={() => handleSaveAnswer(q.id)}
                disabled={savingId === q.id || !answers[q.id]?.trim()}
              >
                {savingId === q.id ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                Save Answer
              </Button>
            </div>
          </div>
        ))}

        {onboardingData?.next_questions?.length === 0 && !onboardingData?.core_complete && (
          <div className="text-center py-8 text-muted-foreground">
            No questions available right now. Keep posting to unlock more!
          </div>
        )}
      </CardContent>

      {onboardingData?.core_complete && (
        <CardFooter className="bg-primary/5 border-t pt-6 flex flex-col items-center gap-4">
          <div className="text-center">
            <h3 className="font-semibold text-lg text-primary">Core Profile Complete!</h3>
            <p className="text-sm text-muted-foreground">You've provided enough data for the LLM to generate your base persona.</p>
          </div>
          <Button 
            size="lg" 
            className="w-full sm:w-auto"
            onClick={handleGeneratePersona}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <><Loader2 className="h-5 w-5 animate-spin mr-2" /> Synthesizing Digital Persona...</>
            ) : (
              <><Sparkles className="h-5 w-5 mr-2" /> Synthesize Digital Persona</>
            )}
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
