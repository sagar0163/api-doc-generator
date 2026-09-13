import { Controller, Get, Post } from '@nestjs/common';

@Controller('api')
export class AppController {
  @Get('users')
  users() {
    return [];
  }

  @Post('users')
  create() {
    return {};
  }
}