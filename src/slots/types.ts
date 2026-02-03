/**
 * Nekazari Odoo ERP Module - Slot Types
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import { ComponentType } from 'react';

export interface SlotWidgetProps {
  selectedEntityId?: string;
  selectedEntityType?: string;
  isLayerActive?: (layerId: string) => boolean;
  onAction?: (action: string, payload: any) => void;
}

export interface ShowWhenCondition {
  entityType?: string[];
  layerActive?: string[];
  hasPermission?: string[];
}

export interface SlotWidgetDefinition {
  id: string;
  moduleId: string;
  component: string;
  priority: number;
  localComponent?: ComponentType<SlotWidgetProps>;
  showWhen?: ShowWhenCondition;
}

export interface ModuleViewerSlots {
  'layer-toggle': SlotWidgetDefinition[];
  'context-panel': SlotWidgetDefinition[];
  'bottom-panel': SlotWidgetDefinition[];
  'entity-tree': SlotWidgetDefinition[];
  'map-layer': SlotWidgetDefinition[];
  moduleProvider?: ComponentType<{ children: React.ReactNode }>;
}
