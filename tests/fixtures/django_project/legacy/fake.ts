// Lets --framework nestjs prove it forces the NestJS scanner even inside a Django tree.
import { Controller, Get } from '@nestjs/common';

@Controller('legacy')
export class LegacyController {
  @Get('items')
  items() {
    return [];
  }
}