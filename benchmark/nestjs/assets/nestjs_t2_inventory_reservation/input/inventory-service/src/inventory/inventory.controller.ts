import { Body, Controller, Get, Post } from '@nestjs/common';
import { InventoryService } from './inventory.service';

interface ReservationBody {
  sku: string;
  quantity: number;
}

@Controller('inventory')
export class InventoryController {
  constructor(private readonly inventoryService: InventoryService) {}

  @Get()
  listItems() {
    return this.inventoryService.listItems();
  }

  @Get('reservations')
  listReservations() {
    return this.inventoryService.listReservations();
  }

  @Post('reservations/commit')
  commitReservation(@Body() body: ReservationBody) {
    return this.inventoryService.commitReservation(body);
  }

  @Post('reservations/rollback')
  rollbackReservation(@Body() body: ReservationBody) {
    return this.inventoryService.rollbackReservation(body);
  }
}
