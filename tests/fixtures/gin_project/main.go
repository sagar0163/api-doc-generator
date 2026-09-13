package main

import "github.com/gin-gonic/gin"

func main() {
	r := gin.Default()
	r.GET("/health", health)
	v1 := r.Group("/api/v1")
	v1.GET("/users", getUsers)
}