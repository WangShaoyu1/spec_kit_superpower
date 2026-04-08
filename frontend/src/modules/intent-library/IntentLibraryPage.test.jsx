import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryPage } from './IntentLibraryPage'


const apiMocks = vi.hoisted(() => ({
  fetchIntentLibraries: vi.fn(),
  createIntentLibrary: vi.fn(),
  deleteIntentLibrary: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const listPayload = {
  items: [
    {
      id: 'lib_001',
      library_key: 'zh_core_v1',
      name: '中文指令库',
      language: 'zh',
      model_count: 1,
      default_thresholds: { command_intent_accuracy_min: 0.95 },
    },
    {
      id: 'lib_002',
      library_key: 'en_core_v1',
      name: '英文指令库',
      language: 'en',
      model_count: 2,
      published_model_id: 'model_002',
      default_thresholds: { command_intent_accuracy_min: 0.96 },
    },
  ],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/intent-library']}>
      <Routes>
        <Route path="/intent-library" element={<IntentLibraryPage token="token-admin" />} />
        <Route path="/intent-library/:libraryId" element={<div>详情页占位</div>} />
      </Routes>
    </MemoryRouter>,
  )
}


describe('IntentLibraryPage', () => {
  beforeEach(() => {
    apiMocks.fetchIntentLibraries.mockResolvedValue(listPayload)
    apiMocks.createIntentLibrary.mockResolvedValue({ library: listPayload.items[0] })
    apiMocks.deleteIntentLibrary.mockResolvedValue({ success: true })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads the library directory and detail view', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '指令库管理' })).toBeInTheDocument()
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: '中文指令库' })).toBeInTheDocument()
      expect(screen.getAllByRole('button', { name: '进入详情' })).toHaveLength(2)
    })

    expect(apiMocks.fetchIntentLibraries).toHaveBeenCalledWith('token-admin')
  })

  it('filters the directory list by name or key on the index page', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '指令库管理' })).toBeInTheDocument()
    })

    fireEvent.change(screen.getByPlaceholderText('按名称或 Key 筛选'), { target: { value: 'en_core' } })

    await waitFor(() => {
      expect(screen.getByText('英文指令库')).toBeInTheDocument()
      expect(screen.queryByText('中文指令库')).not.toBeInTheDocument()
    })
  })

  it('creates a library and navigates to the dedicated detail page', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '新建指令库' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建指令库' }))
    fireEvent.change(screen.getByLabelText('唯一 Key'), { target: { value: 'zh_core_v2' } })
    fireEvent.change(screen.getByLabelText('名称'), { target: { value: '中文指令库 2' } })
    fireEvent.click(screen.getByRole('button', { name: /创\s*建/ }))

    await waitFor(() => {
      expect(apiMocks.createIntentLibrary).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('详情页占位')).toBeInTheDocument()
    })
  })

  it('shows a field error when library_key is duplicated', async () => {
    apiMocks.createIntentLibrary.mockRejectedValueOnce(new Error('指令库 Key 已存在，请更换后重试'))
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '新建指令库' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建指令库' }))
    fireEvent.change(screen.getByLabelText('唯一 Key'), { target: { value: 'zh_core_v1' } })
    fireEvent.change(screen.getByLabelText('名称'), { target: { value: '重复库' } })
    fireEvent.click(screen.getByRole('button', { name: /创\s*建/ }))

    await waitFor(() => {
      expect(screen.getByText('指令库 Key 已存在，请更换后重试')).toBeInTheDocument()
    })
  })

  it('deletes a library and reloads the directory', async () => {
    apiMocks.fetchIntentLibraries
      .mockResolvedValueOnce(listPayload)
      .mockResolvedValueOnce({ items: [listPayload.items[1]] })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('中文指令库')).toBeInTheDocument()
    })

    fireEvent.click(screen.getAllByRole('button', { name: '删除' })[0])

    await waitFor(() => {
      expect(apiMocks.deleteIntentLibrary).toHaveBeenCalledWith('token-admin', 'lib_001')
      expect(screen.queryByText('中文指令库')).not.toBeInTheDocument()
      expect(screen.getByText('英文指令库')).toBeInTheDocument()
    })
  })

  it('disables delete for libraries that already have a published model', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('英文指令库')).toBeInTheDocument()
    })

    expect(screen.getAllByRole('button', { name: '删除' })[1]).toBeDisabled()
  })
})
