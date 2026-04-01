import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryPage } from './IntentLibraryPage'


const apiMocks = vi.hoisted(() => ({
  fetchIntentLibraries: vi.fn(),
  createIntentLibrary: vi.fn(),
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
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads the library directory and detail view', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '指令库管理' })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: '中文指令库' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '进入详情' })).toBeInTheDocument()
    })

    expect(apiMocks.fetchIntentLibraries).toHaveBeenCalledWith('token-admin')
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
})
