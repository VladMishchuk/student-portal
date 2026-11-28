import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GradeForm from '../components/GradeForm.vue'

function respond(status, data) {
  return vi.fn().mockResolvedValue({
    ok: status < 400,
    status,
    json: async () => data,
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('GradeForm', () => {
  it('надсилає оцінку числом без пробілів у назві і повідомляє про створення', async () => {
    const created = {
      id: 10,
      student: 5,
      course: 'Програмування',
      score: 88,
      ects: 'B',
      graded_on: '2026-11-28',
    }
    const fetchMock = respond(201, created)
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(GradeForm, { props: { studentId: 5 } })
    await wrapper.find('input:not([type])').setValue('  Програмування  ')
    await wrapper.find('input[type="number"]').setValue('88')
    await wrapper.find('input[type="date"]').setValue('2026-11-28')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const [, options] = fetchMock.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({
      course: 'Програмування',
      score: 88,
      graded_on: '2026-11-28',
      student: 5,
    })
    expect(wrapper.emitted('created')).toEqual([[created]])
  })

  it('показує помилку 400 біля поля', async () => {
    const message = 'Переконайтеся, що це значення менше або дорівнює 100.'
    vi.stubGlobal('fetch', respond(400, { score: [message] }))

    const wrapper = mount(GradeForm, { props: { studentId: 5 } })
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error').text()).toBe(message)
    expect(wrapper.emitted('created')).toBeUndefined()
  })
})
