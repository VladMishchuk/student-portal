import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StudentForm from '../components/StudentForm.vue'

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

describe('StudentForm', () => {
  it('надсилає студента і повідомляє про створення', async () => {
    const created = { id: 9, first_name: 'Тарас', last_name: 'Гнатюк', group: 1, average: null, grades: [] }
    const fetchMock = respond(201, created)
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(StudentForm, { props: { groupId: 1 } })
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('  Гнатюк  ')
    await inputs[1].setValue('  Тарас  ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const [, options] = fetchMock.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({
      last_name: 'Гнатюк',
      first_name: 'Тарас',
      group: 1,
    })
    expect(wrapper.emitted('created')).toEqual([[created]])
  })

  it('показує помилки перевірки біля полів', async () => {
    const message = 'Це поле не може бути порожнім.'
    vi.stubGlobal('fetch', respond(400, { last_name: [message] }))

    const wrapper = mount(StudentForm, { props: { groupId: 1 } })
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.error').text()).toBe(message)
    expect(wrapper.emitted('created')).toBeUndefined()
  })
})
