import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import App from '../App.vue'

const KOVAL = {
  id: 1,
  first_name: 'Олена',
  last_name: 'Коваль',
  group: 1,
  average: 91.5,
  grades: [{ id: 1, student: 1, course: 'Математика', score: 91, ects: 'A', graded_on: '2026-11-20' }],
}

function server(permissions, extraRoutes = {}) {
  const routes = {
    'GET /api/me/': [200, { username: 'user', permissions }],
    'GET /api/students/': [200, { count: 1, next: null, results: [KOVAL] }],
    ...extraRoutes,
  }
  return vi.fn(async (url, options = {}) => {
    const [status, data] = routes[`${options.method ?? 'GET'} ${url}`] ?? [404, {}]
    return { ok: status < 400, status, json: async () => data }
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('викладач бачить форму оцінки, але не видалення і не редагування', async () => {
    vi.stubGlobal('fetch', server(['add_grade', 'view_grade', 'view_student']))
    const wrapper = mount(App)
    await flushPromises()

    const labels = () => wrapper.findAll('button').map((b) => b.text())
    expect(labels()).not.toContain('Видалити')
    expect(wrapper.text()).not.toContain('Новий студент')

    await wrapper.find('td button').trigger('click')
    expect(wrapper.text()).toContain('Нова оцінка')
    expect(labels()).not.toContain('Редагувати')
  })

  it('деканат бачить видалення, нового студента і редагування, але не форму оцінки', async () => {
    vi.stubGlobal(
      'fetch',
      server(['add_student', 'change_student', 'delete_student', 'view_student', 'view_grade']),
    )
    const wrapper = mount(App)
    await flushPromises()

    const labels = () => wrapper.findAll('button').map((b) => b.text())
    expect(labels()).toContain('Видалити')
    expect(wrapper.text()).toContain('Новий студент')

    await wrapper.find('td button').trigger('click')
    expect(labels()).toContain('Редагувати')
    expect(wrapper.text()).not.toContain('Нова оцінка')
  })

  it('анонімний користувач бачить запрошення увійти', async () => {
    vi.stubGlobal(
      'fetch',
      server([], {
        'GET /api/me/': [403, { detail: 'Не ввійшли' }],
        'GET /api/students/': [403, { detail: 'Не ввійшли' }],
      }),
    )
    const wrapper = mount(App)
    await flushPromises()

    expect(wrapper.text()).toContain('Увійдіть на сайт')
  })

  it('варіант 3: деканат змінює прізвище та ім’я студента через PATCH і оновлює рядок таблиці', async () => {
    const updated = { ...KOVAL, last_name: 'Коваленко', first_name: 'Ольга' }
    const fetchMock = server(
      ['change_student', 'view_student', 'view_grade'],
      { 'PATCH /api/students/1/': [200, updated] },
    )
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(App)
    await flushPromises()

    await wrapper.find('td button').trigger('click')
    await wrapper.findAll('button').find((b) => b.text() === 'Редагувати').trigger('click')

    const inputs = wrapper.findAll('.edit-form input')
    await inputs[0].setValue('Коваленко')
    await inputs[1].setValue('Ольга')
    await wrapper.find('.edit-form').trigger('submit')
    await flushPromises()

    const patchCall = fetchMock.mock.calls.find(
      ([url, opts]) => url === '/api/students/1/' && opts?.method === 'PATCH',
    )
    expect(patchCall).toBeDefined()
    expect(JSON.parse(patchCall[1].body)).toEqual({
      last_name: 'Коваленко',
      first_name: 'Ольга',
    })
    expect(wrapper.find('td button').text()).toBe('Коваленко Ольга')
  })
})
