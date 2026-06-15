<script setup>
import { RouterLink } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import { useAuth } from '../stores/auth'
import { useHomeDashboard } from '../composables/useHomeDashboard'
import { usePushNotifications } from '../composables/usePushNotifications'
import PushBanner from '../components/home/PushBanner.vue'
import ActionHero from '../components/home/ActionHero.vue'
import DashboardSummary from '../components/home/DashboardSummary.vue'
import SectorListItem from '../components/home/SectorListItem.vue'

const { user } = useAuth()
const { fields, loading, todayLabel, activeFields, activeSectors, totalArea, urgentSector, urgentCount } = useHomeDashboard()
const { pushStatus, enableNotifications } = usePushNotifications()
</script>

<template>
    <div class="max-w-[1180px] mx-auto px-5 md:px-8 pt-3 md:pt-8 pb-8">

      <!-- Header -->
      <div class="flex justify-between items-start md:items-end mb-5 md:mb-7">
          <div>
              <div class="app-label mb-1">{{ todayLabel }}</div>
              <h1 class="text-[26px] md:text-[38px] font-bold text-ink tracking-tight leading-tight m-0">
                  Hola, {{ user?.name || 'Productor' }}.
              </h1>
          </div>
      </div>

      <PushBanner v-if="pushStatus === 'idle'" @enable="enableNotifications" />

      <!-- Two-column en desktop · una columna en mobile -->
      <div class="grid md:grid-cols-[1.4fr_1fr] gap-4 mb-7">
          <ActionHero :urgent-sector="urgentSector" :urgent-count="urgentCount" :active-count="activeSectors.length" />
          <DashboardSummary :active-fields-count="activeFields.length" :total-area="totalArea" />
      </div>

      <!-- Lista de campos -->
      <div class="flex items-center justify-between px-1 mb-2.5">
          <div class="app-label">Mis campos</div>
      </div>

      <div v-if="loading" class="text-center py-12 text-muted text-sm">Cargando...</div>
      <div v-else-if="fields.length === 0" class="bg-surface border border-line rounded-3xl p-6 text-center">
          <p class="text-muted text-sm mb-3">Aún no registraste tu primer campo.</p>
          <RouterLink to="/fields/new" class="inline-flex items-center gap-1.5 bg-primary text-white font-bold text-sm px-4 py-2.5 rounded-xl">
              <Plus :size="14" /> Registrar campo
          </RouterLink>
      </div>

      <div v-else class="grid md:grid-cols-2 gap-3">
          <SectorListItem v-for="s in activeSectors" :key="s.id" :sector="s" />
      </div>
    </div>
</template>