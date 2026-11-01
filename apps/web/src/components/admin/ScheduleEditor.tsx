import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { DayScheduleIn, DayScheduleOut, WeeklyScheduleUpdate } from '@/lib/admin-api-types'

export const WEEKDAY_LABELS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export interface EditableDay {
  weekday: number
  working: boolean
  start_time: string
  end_time: string
  breaks: { start_time: string; end_time: string }[]
}

/** Builds one row per weekday (0=Mon..6=Sun), pre-filled from whatever the
 * server already has configured, and "off" for any weekday it didn't return. */
export function scheduleOutToEditableDays(schedule: DayScheduleOut[]): EditableDay[] {
  const byWeekday = new Map(schedule.map((d) => [d.weekday, d]))
  return Array.from({ length: 7 }, (_, weekday) => {
    const existing = byWeekday.get(weekday)
    return existing
      ? { weekday, working: true, start_time: existing.start_time, end_time: existing.end_time, breaks: existing.breaks }
      : { weekday, working: false, start_time: '09:00', end_time: '18:00', breaks: [] }
  })
}

export function editableDaysToWeeklyScheduleUpdate(days: EditableDay[]): WeeklyScheduleUpdate {
  const out: DayScheduleIn[] = days
    .filter((d) => d.working)
    .map((d) => ({ weekday: d.weekday, start_time: d.start_time, end_time: d.end_time, breaks: d.breaks }))
  return { days: out }
}

/** A weekly schedule editor: one row per weekday, a working-hours toggle,
 * start/end times, and any number of recurring breaks. Used both for a
 * single staff member's hours and for the business's own operating hours
 * (the backend models both the same way — see app/models/schedule.py). */
export function ScheduleEditor({
  days,
  onChange,
}: {
  days: EditableDay[]
  onChange: (days: EditableDay[]) => void
}) {
  function updateDay(weekday: number, patch: Partial<EditableDay>) {
    onChange(days.map((d) => (d.weekday === weekday ? { ...d, ...patch } : d)))
  }

  function addBreak(weekday: number) {
    const day = days.find((d) => d.weekday === weekday)!
    updateDay(weekday, { breaks: [...day.breaks, { start_time: '13:00', end_time: '14:00' }] })
  }

  function removeBreak(weekday: number, index: number) {
    const day = days.find((d) => d.weekday === weekday)!
    updateDay(weekday, { breaks: day.breaks.filter((_, i) => i !== index) })
  }

  return (
    <div className="space-y-4">
      {days.map((day) => (
        <div key={day.weekday} className="rounded-[var(--radius-control)] border border-charcoal-100 p-3">
          <label className="flex items-center gap-2 text-sm font-medium text-charcoal-900">
            <input
              type="checkbox"
              checked={day.working}
              onChange={(e) => updateDay(day.weekday, { working: e.target.checked })}
            />
            {WEEKDAY_LABELS[day.weekday]}
          </label>

          {day.working && (
            <div className="mt-2.5 space-y-2.5 pl-6">
              <div className="flex items-center gap-2">
                <Input
                  type="time"
                  value={day.start_time}
                  onChange={(e) => updateDay(day.weekday, { start_time: e.target.value })}
                  className="w-36"
                />
                <span className="text-sm text-charcoal-500">to</span>
                <Input
                  type="time"
                  value={day.end_time}
                  onChange={(e) => updateDay(day.weekday, { end_time: e.target.value })}
                  className="w-36"
                />
              </div>

              {day.breaks.map((brk, i) => (
                <div key={i} className="flex items-center gap-2 pl-2">
                  <span className="text-xs text-charcoal-500">Break</span>
                  <Input
                    type="time"
                    value={brk.start_time}
                    onChange={(e) => {
                      const breaks = [...day.breaks]
                      breaks[i] = { ...breaks[i], start_time: e.target.value }
                      updateDay(day.weekday, { breaks })
                    }}
                    className="w-32"
                  />
                  <span className="text-xs text-charcoal-500">to</span>
                  <Input
                    type="time"
                    value={brk.end_time}
                    onChange={(e) => {
                      const breaks = [...day.breaks]
                      breaks[i] = { ...breaks[i], end_time: e.target.value }
                      updateDay(day.weekday, { breaks })
                    }}
                    className="w-32"
                  />
                  <button
                    type="button"
                    onClick={() => removeBreak(day.weekday, i)}
                    className="text-charcoal-500 hover:text-status-cancelled"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              ))}
              <Button type="button" variant="ghost" size="sm" onClick={() => addBreak(day.weekday)}>
                <Plus /> Add break
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
