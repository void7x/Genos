/** Production Genos service singleton. */
import { createHttpBackedService } from './transport'
import { realGenosTransport } from './realTransport'
import type { GenosService } from './types'

export const genosService: GenosService = createHttpBackedService(realGenosTransport)

export type { GenosService } from './types'
